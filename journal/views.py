from django.shortcuts import render
from django.shortcuts import redirect
from journal.forms import JournalEntryForm
from django.http.request import HttpRequest
from django.contrib.auth.decorators import login_required
from journal.models import JournalEntry
from django.shortcuts import get_object_or_404
from django.http.response import JsonResponse
from django.core.serializers import serialize
import json
from django.views.decorators.http import require_http_methods


@login_required
def journal(request: HttpRequest):
    form = JournalEntryForm(request.POST or None)
    context = {}

    if request.method == "POST":
        if form.is_valid():
            entry = form.save(commit=False)
            entry.user = request.user
            entry.save()
            return redirect("journal")

        context["msg"] = "Invalid Input"

    # Get all entries for the user, ordered by most recent first
    past_entries = JournalEntry.objects.filter(user=request.user).order_by('-entry_date')
    
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
