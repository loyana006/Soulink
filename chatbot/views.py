import json
import requests
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.contrib.auth.decorators import login_required
from journal.models import JournalEntry
from journal.sentiment import extract_emotional_state
from django.shortcuts import get_object_or_404, render, redirect
from .models import ChatMessage, ChatSession


# Crisis keywords that trigger safety helpline suggestions
CRISIS_KEYWORDS = [
    'kill', 'suicide', 'suicidal', 'end my life', 'want to die', 'hurt myself',
    'self-harm', 'self harm', 'cutting', 'cut myself', 'end it all',
    'no reason to live', 'better off dead', 'take my life', 'end myself',
]

SAFETY_HELPLINES = (
    "If you're in crisis, please reach out for help:\n"
    "• National Suicide Prevention Lifeline (NP): 1166\n"
    "• International Association for Suicide Prevention: https://www.iasp.info/resources/Crisis_Centres/"
)


def _contains_crisis_keywords(text):
    """Check if message contains crisis-related keywords."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in CRISIS_KEYWORDS)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def chat_with_yana(request):
    """
    API endpoint to communicate with RASA chatbot.
    Sends user message to RASA server and returns bot response.
    If crisis keywords are detected, appends safety helpline information.
    """
    try:
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        sender_id = str(request.user.id)  # Use user ID as sender ID for session tracking
        
        if not message:
            return JsonResponse({
                'error': 'Message is required'
            }, status=400)
        
        # Determine or create current chat session
        session_pk = request.session.get("yana_session_pk")
        chat_session = None
        if session_pk:
            chat_session = ChatSession.objects.filter(
                id=session_pk, user=request.user
            ).first()
        # Backwards compatibility with older string-based session id (if present)
        if not chat_session:
            chat_session = ChatSession.objects.create(user=request.user)
            request.session["yana_session_pk"] = chat_session.pk

        # RASA server configuration
        rasa_server_url = getattr(settings, 'RASA_SERVER_URL', 'http://localhost:5005')
        rasa_webhook = f"{rasa_server_url}/webhooks/rest/webhook"
        
        # Prepare payload for RASA
        payload = {
            "sender": sender_id,
            "message": message
        }
        
        # Send request to RASA server
        try:
            response = requests.post(
                rasa_webhook,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            rasa_response = response.json()
            
            # Extract bot response from RASA
            if rasa_response and len(rasa_response) > 0:
                bot_message = rasa_response[0].get('text', 'I apologize, but I didn\'t understand that. Could you rephrase?')
            else:
                bot_message = 'I\'m here to listen. Could you tell me more?'

            # If crisis keywords detected, append safety helpline information
            if _contains_crisis_keywords(message):
                bot_message = (
                    bot_message + "\n\n" + SAFETY_HELPLINES
                )

            # Persist chat messages (user + yana) to database
            ChatMessage.objects.create(
                user=request.user,
                text=message,
                role=ChatMessage.ROLE_USER,
                session=chat_session,
            )
            ChatMessage.objects.create(
                user=request.user,
                text=bot_message,
                role=ChatMessage.ROLE_YANA,
                session=chat_session,
            )
            snippet = message[:220] + ("…" if len(message) > 220 else "")
            ChatSession.objects.filter(pk=chat_session.pk).update(
                topic_summary=f"Recent focus: {snippet}"
            )

            return JsonResponse({
                'success': True,
                'message': bot_message,
                'sender': 'yana'
            })
            
        except requests.exceptions.RequestException as e:
            # If RASA server is not available, return a fallback response
            fallback_message = 'I\'m here to listen and support you. Could you tell me more about what you\'re feeling?'
            if _contains_crisis_keywords(message):
                fallback_message = fallback_message + "\n\n" + SAFETY_HELPLINES

            # Persist user and fallback bot message
            ChatMessage.objects.create(
                user=request.user,
                text=message,
                role=ChatMessage.ROLE_USER,
                session=chat_session,
            )
            ChatMessage.objects.create(
                user=request.user,
                text=fallback_message,
                role=ChatMessage.ROLE_YANA,
                session=chat_session,
            )
            snippet = message[:220] + ("…" if len(message) > 220 else "")
            ChatSession.objects.filter(pk=chat_session.pk).update(
                topic_summary=f"Recent focus: {snippet}"
            )

            return JsonResponse({
                'success': True,
                'message': fallback_message,
                'sender': 'yana',
                'note': 'RASA server unavailable, using fallback response'
            })
            
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': f'An error occurred: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def reset_conversation(request):
    """
    Reset the conversation session with RASA.
    """
    try:
        sender_id = str(request.user.id)
        rasa_server_url = getattr(settings, 'RASA_SERVER_URL', 'http://localhost:5005')
        rasa_conversation_endpoint = f"{rasa_server_url}/conversations/{sender_id}/tracker/events"
        
        # Send a restart event to RASA
        payload = {
            "event": "restart"
        }
        
        try:
            response = requests.post(
                rasa_conversation_endpoint,
                json=payload,
                timeout=5
            )
            response.raise_for_status()

            # Mark current chat session as inactive and clear session key
            session_pk = request.session.pop("yana_session_pk", None)
            if session_pk:
                ChatSession.objects.filter(id=session_pk, user=request.user).update(
                    is_active=False
                )

            return JsonResponse({
                'success': True,
                'message': 'Conversation reset successfully'
            })
        except requests.exceptions.RequestException:
            # If RASA is unavailable, still return success
            # Still clear local session grouping and mark session inactive
            session_pk = request.session.pop("yana_session_pk", None)
            if session_pk:
                ChatSession.objects.filter(id=session_pk, user=request.user).update(
                    is_active=False
                )

            return JsonResponse({
                'success': True,
                'message': 'Conversation reset'
            })
            
    except Exception as e:
        return JsonResponse({
            'error': f'An error occurred: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def edit_session_title(request, session_id):
    """
    Update the title of a chat session.
    """
    try:
        session = get_object_or_404(ChatSession, id=session_id, user=request.user)
        data = json.loads(request.body)
        title = (data.get("title") or "").strip()
        session.title = title or "Untitled chat"
        session.save(update_fields=["title", "updated_at"])
        return JsonResponse({"success": True, "title": session.title})
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def delete_session(request, session_id):
    """
    Delete a chat session and all its messages.
    """
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)

    # If this session is currently active in the browser, clear it
    active_pk = request.session.get("yana_session_pk")
    if active_pk and int(active_pk) == session.id:
        request.session.pop("yana_session_pk", None)

    session.delete()
    return JsonResponse({"success": True})


@login_required
@require_http_methods(["GET"])
def activate_session(request, session_id):
    """
    Mark a given session as the active one and redirect to the chat page
    so the user can continue that conversation.
    """
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    request.session["yana_session_pk"] = session.id
    # Ensure the session is marked active
    if not session.is_active:
        session.is_active = True
        session.save(update_fields=["is_active", "updated_at"])
    return redirect("yana")


@login_required
@require_http_methods(["GET"])
def yana_history(request):
    """
    Render a page with the user's recent chat history with Yana.
    """
    sessions = (
        ChatSession.objects.filter(user=request.user)
        .prefetch_related("messages")
        .order_by("-updated_at")
    )

    return render(
        request,
        "yana_history.html",
        {
            "sessions": sessions,
        },
    )


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def analyze_journal_entry(request):
    """
    Analyze a journal entry using RASA to provide emotional state summary.
    """
    try:
        data = json.loads(request.body)
        entry_id = data.get('entry_id')
        
        if not entry_id:
            return JsonResponse({
                'error': 'Entry ID is required'
            }, status=400)
        
        # Get the journal entry
        entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)
        
        # Prepare journal text for analysis
        journal_text = f"{entry.title}. {entry.entry}"
        sender_id = f"journal_analysis_{request.user.id}_{entry_id}"
        
        # RASA server configuration
        rasa_server_url = getattr(settings, 'RASA_SERVER_URL', 'http://localhost:5005')
        rasa_webhook = f"{rasa_server_url}/webhooks/rest/webhook"
        
        # Prepare payload for RASA with journal entry
        payload = {
            "sender": sender_id,
            "message": f"Analyze this journal entry and provide an emotional state summary: {journal_text}"
        }
        
        # Send request to RASA server
        try:
            response = requests.post(
                rasa_webhook,
                json=payload,
                timeout=15
            )
            response.raise_for_status()
            rasa_response = response.json()
            
            # Extract bot response from RASA
            if rasa_response and len(rasa_response) > 0:
                analysis = rasa_response[0].get('text', 'Unable to analyze entry at this time.')
            else:
                analysis = 'Unable to analyze entry at this time.'
            
            # Extract emotional insights (you can enhance this with custom RASA actions)
            emotional_state = extract_emotional_state(journal_text)
            
            return JsonResponse({
                'success': True,
                'analysis': analysis,
                'emotional_state': emotional_state,
                'entry_id': entry_id
            })
            
        except requests.exceptions.RequestException as e:
            # If RASA server is not available, provide basic analysis
            emotional_state = extract_emotional_state(journal_text)
            return JsonResponse({
                'success': True,
                'analysis': 'Based on your journal entry, I can see you\'re expressing your thoughts and feelings. This is a positive step in self-reflection and emotional awareness.',
                'emotional_state': emotional_state,
                'entry_id': entry_id,
                'note': 'RASA server unavailable, using fallback analysis'
            })
            
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': f'An error occurred: {str(e)}'
        }, status=500)
