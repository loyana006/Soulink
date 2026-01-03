from django.shortcuts import render


def index(request):
    return render(request, "index.html")


def about(request):
    return render(request, "about.html")


def support(request):
    return render(request, "support.html")


def chatbot(request):
    return render(request, "yana.html")


def confessionals(request):
    return render(request, "confessionals.html")


def blog(request):
    return render(request, "blog.html")


def journal(request):
    return render(request, "journal.html")


def dashboard(request):
    return render(request, "dashboard.html")
