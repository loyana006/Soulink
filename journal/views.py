from django.shortcuts import render, redirect
from journal.forms import JournalEntryForm
from django.http import HttpRequest, JsonResponse
from django.contrib.auth.decorators import login_required
from journal.models import JournalEntry
from django.shortcuts import get_object_or_404
import json
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt


@login_required
def journal(request: HttpRequest):
    form = JournalEntryForm(request.POST or None)
    context = {}

    if request.method == "POST":
        if form.is_valid():
            entry = form.save(commit=False)
            entry.user = request.user
            entry.save()
            # Clear draft after successful save
            if "journal_draft" in request.session:
                del request.session["journal_draft"]
            return redirect("journal")

        context["msg"] = "Invalid Input"

    # Get all entries for the user, ordered by most recent first
    past_entries = JournalEntry.objects.filter(user=request.user).order_by('-entry_date')

    # Include any saved draft from session for restore (as JSON for template)
    draft = request.session.get("journal_draft") or {}
    context["journal_draft_json"] = mark_safe(json.dumps(draft))
    context["form"] = form
    context["past_entries"] = past_entries
    context["total_entries"] = past_entries.count()

    return render(request, "journal.html", context)


@login_required
def get_journal_entry(request: HttpRequest, id=None):
    """Get a single journal entry as JSON with all necessary data"""
    if request.method == "GET" and id:
        entry = get_object_or_404(JournalEntry, id=id, user=request.user)
        
        # Build comprehensive response with all necessary data
        data = {
            "id": entry.id,
            "title": entry.title,
            "entry": entry.entry,
            "entry_date": entry.entry_date.isoformat() if entry.entry_date else None,
            "created_at": entry.entry_date.isoformat() if entry.entry_date else None,
            "updated_at": entry.entry_date.isoformat() if entry.entry_date else None,  # Note: model doesn't have updated_at field
            "word_count": entry.word_count,
            "read_time": entry.read_time,
            "user_id": entry.user.id,
        }
        
        return JsonResponse(data)

    return JsonResponse({"error": "Entry ID required"}, status=400)


@login_required
def view_journal_entry(request: HttpRequest, id=None):
    """View a single journal entry with RASA analysis"""
    if not id:
        return redirect("journal")
    
    entry = get_object_or_404(JournalEntry, id=id, user=request.user)
    
    context = {
        "entry": entry,
    }
    
    return render(request, "journal_entry_view.html", context)


@login_required
@require_http_methods(["DELETE"])
def delete_journal_entry(request, id=None):
    """Delete a journal entry - only allows deletion of user's own entries"""
    try:
        # Security: Ensure user can only delete their own entries
        entry = get_object_or_404(JournalEntry, id=id, user=request.user)
        entry.delete()

        return JsonResponse(
            {"success": True, "message": "Journal entry deleted successfully"}
        )

    except JournalEntry.DoesNotExist:
        return JsonResponse({"error": "Entry not found"}, status=404)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def auto_save_draft(request):
    """
    Save journal draft to session. Used when user is typing in the add-entry modal
    to prevent data loss. Draft is stored in session and can be restored.
    """
    try:
        data = json.loads(request.body)
        title = (data.get("title") or "").strip()[:200]
        entry = (data.get("entry") or "").strip()[:50000]

        request.session["journal_draft"] = {"title": title, "entry": entry}
        request.session.modified = True
        return JsonResponse({"success": True})
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
