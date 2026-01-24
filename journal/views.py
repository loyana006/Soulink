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

    context["form"] = form
    context["past_entries"] = JournalEntry.objects.all().filter(user=request.user.id)

    return render(request, "journal.html", context)


@login_required
def get_journal_entry(request: HttpRequest, id=None):
    entry = None

    if request.method == "GET" and id:
        entry = get_object_or_404(JournalEntry, id=id, user=request.user)
        serialized_data = serialize("json", [entry])
        data = json.loads(serialized_data)[0]["fields"]
        return JsonResponse(data)

    return JsonResponse({})


@login_required
@require_http_methods(["DELETE"])
def delete_journal_entry(request, id=None):
    """Delete a journal entry"""
    try:
        entry = get_object_or_404(JournalEntry, id=id)
        entry.delete()

        return JsonResponse(
            {"success": True, "message": "Journal entry deleted successfully"}
        )

    except JournalEntry.DoesNotExist:
        return JsonResponse({"error": "Entry not found"}, status=404)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
