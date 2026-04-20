import json
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from journal.forms import JournalEntryForm
from journal.models import JournalEntry

from accounts.models import UserGoal, UserProfile
from accounts.profile_data import ensure_badges, week_start
from journal.sentiment import extract_emotional_state

ENTRIES_PAGE_SIZE = 12


def _entries_queryset(user):
    return JournalEntry.objects.filter(user=user).order_by("-entry_date", "-id")


def _entries_batch(qs, before_date: datetime | None = None, before_id: int | None = None):
    """
    Cursor pagination by (entry_date, id) descending.
    If before_date/before_id are provided, returns entries strictly older than that cursor.
    """
    if before_date is not None and before_id is not None:
        cursor_dt = timezone.make_aware(before_date) if timezone.is_naive(before_date) else before_date
        qs = qs.filter(Q(entry_date__lt=cursor_dt) | Q(entry_date=cursor_dt, id__lt=before_id))
    chunk = list(qs[: ENTRIES_PAGE_SIZE + 1])
    has_more = len(chunk) > ENTRIES_PAGE_SIZE
    if has_more:
        chunk = chunk[:ENTRIES_PAGE_SIZE]
    return chunk, has_more


@login_required
def journal(request: HttpRequest):
    form = JournalEntryForm(request.POST or None)
    context = {}

    if request.method == "POST":
        if form.is_valid():
            entry = form.save(commit=False)
            entry.user = request.user
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
            if profile.ai_journal_analysis_consent:
                text = f"{entry.title} {entry.entry}"
                entry.sentiment_analysis = extract_emotional_state(text)
            else:
                entry.sentiment_analysis = None
            entry.save()
            ensure_badges(request.user)
            ws = week_start(timezone.localdate())
            goal, _ = UserGoal.objects.get_or_create(
                user=request.user,
                week_start=ws,
                defaults={"target_entries": 3, "progress": 0},
            )
            goal.progress = min(goal.progress + 1, goal.target_entries)
            goal.save(update_fields=["progress"])
            # Clear draft after successful save
            if "journal_draft" in request.session:
                del request.session["journal_draft"]
            return redirect("journal")

        context["msg"] = "Invalid Input"

    entries_qs = _entries_queryset(request.user)
    past_entries, entries_has_more = _entries_batch(entries_qs)
    entries_next_before_date = (
        timezone.localtime(past_entries[-1].entry_date).isoformat() if past_entries and entries_has_more else ""
    )
    entries_next_before_id = past_entries[-1].id if past_entries and entries_has_more else ""

    # Include any saved draft from session for restore (as JSON for template)
    draft = request.session.get("journal_draft") or {}
    context["journal_draft_json"] = mark_safe(json.dumps(draft))
    context["form"] = form
    context["past_entries"] = past_entries
    context["total_entries"] = entries_qs.count()
    context["entries_has_more"] = entries_has_more
    context["entries_next_before_date"] = entries_next_before_date
    context["entries_next_before_id"] = entries_next_before_id

    return render(request, "journal.html", context)


@login_required
@require_http_methods(["GET"])
def journal_entries_more(request: HttpRequest):
    """JSON fragment for appending older journal entries (Load more)."""
    raw_date = request.GET.get("before_date", "")
    raw_id = request.GET.get("before_id", "")
    try:
        before_id = int(raw_id)
    except (TypeError, ValueError):
        return JsonResponse({"error": "Invalid or missing before_id"}, status=400)

    try:
        # Accept both "Z" and "+00:00" forms
        raw_date_norm = raw_date.replace("Z", "+00:00")
        before_date = datetime.fromisoformat(raw_date_norm)
    except Exception:
        return JsonResponse({"error": "Invalid or missing before_date"}, status=400)

    batch, has_more = _entries_batch(
        _entries_queryset(request.user),
        before_date=before_date,
        before_id=before_id,
    )

    html_parts = []
    for entry in batch:
        html_parts.append(
            render_to_string(
                "journal/_entry_card.html",
                {"entry": entry},
                request=request,
            )
        )

    next_before_date = (
        timezone.localtime(batch[-1].entry_date).isoformat() if batch and has_more else None
    )
    next_before_id = batch[-1].id if batch and has_more else None

    return JsonResponse(
        {
            "html": "".join(html_parts),
            "has_more": has_more,
            "next_before_date": next_before_date,
            "next_before_id": next_before_id,
        }
    )


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
