from django.shortcuts import render


def index(request):
    return render(request, "index.html")


def about(request):
    return render(request, "about.html")


def support(request):
    return render(request, "support.html")


def chatbot(request):
    return render(request, "yana.html")


def dashboard(request):
    from blog.models import BlogPost

    recent_blog_posts = BlogPost.objects.filter(is_published=True).order_by(
        "-published_at"
    )[:3]
    return render(
        request,
        "dashboard.html",
        {"recent_blog_posts": recent_blog_posts},
    )
