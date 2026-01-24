from django.http.request import HttpRequest
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from confession.models import ConfessionModal
from confession.forms import ConfessionEntryForm


@login_required
def confessions(request: HttpRequest):
    context = {}
    form = ConfessionEntryForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            entry = form.save(commit=False)
            entry.user = request.user
            entry.save()

    context["form"] = form
    context["confessions"] = ConfessionModal.objects.all()
    return render(request, "confessionals.html", context)
