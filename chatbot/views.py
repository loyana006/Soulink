import json
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.contrib.auth.decorators import login_required
from journal.models import JournalEntry
from django.shortcuts import get_object_or_404


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def chat_with_yana(request):
    """
    API endpoint to communicate with RASA chatbot.
    Sends user message to RASA server and returns bot response.
    """
    try:
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        sender_id = str(request.user.id)  # Use user ID as sender ID for session tracking
        
        if not message:
            return JsonResponse({
                'error': 'Message is required'
            }, status=400)
        
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
            
            return JsonResponse({
                'success': True,
                'message': bot_message,
                'sender': 'yana'
            })
            
        except requests.exceptions.RequestException as e:
            # If RASA server is not available, return a fallback response
            return JsonResponse({
                'success': True,
                'message': 'I\'m here to listen and support you. Could you tell me more about what you\'re feeling?',
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
            
            return JsonResponse({
                'success': True,
                'message': 'Conversation reset successfully'
            })
        except requests.exceptions.RequestException:
            # If RASA is unavailable, still return success
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


def extract_emotional_state(text):
    """
    Extract basic emotional state from journal text using keyword analysis.
    This is a fallback method when RASA is not available.
    """
    text_lower = text.lower()
    
    # Emotional keywords
    positive_keywords = ['happy', 'joy', 'grateful', 'thankful', 'excited', 'proud', 'content', 'peaceful', 'calm', 'hopeful', 'optimistic', 'love', 'appreciate']
    negative_keywords = ['sad', 'depressed', 'anxious', 'worried', 'stressed', 'angry', 'frustrated', 'overwhelmed', 'lonely', 'hurt', 'disappointed', 'fear', 'scared']
    neutral_keywords = ['okay', 'fine', 'normal', 'alright', 'neutral']
    
    positive_count = sum(1 for word in positive_keywords if word in text_lower)
    negative_count = sum(1 for word in negative_keywords if word in text_lower)
    neutral_count = sum(1 for word in neutral_keywords if word in text_lower)
    
    if positive_count > negative_count and positive_count > 0:
        state = 'positive'
        confidence = min(positive_count / (positive_count + negative_count + 1), 1.0)
    elif negative_count > positive_count and negative_count > 0:
        state = 'negative'
        confidence = min(negative_count / (positive_count + negative_count + 1), 1.0)
    elif neutral_count > 0:
        state = 'neutral'
        confidence = 0.5
    else:
        state = 'mixed'
        confidence = 0.3
    
    return {
        'state': state,
        'confidence': round(confidence, 2),
        'positive_indicators': positive_count,
        'negative_indicators': negative_count
    }
