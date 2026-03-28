import json
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .forms import (
    LoginForm,
    PasswordChangeForm,
    UserSignUpForm,
)
from .backends import EmailOrUsernameBackend
from .models import UserGoal, UserProfile
from .profile_data import (
    chat_recaps,
    ensure_badges,
    heatmap_days,
    journal_keyword_cloud,
    memory_this_time_last_year,
    monthly_journal_insight,
    sentiment_chart_series,
    week_start,
)


def login_view(request):
    msg = None
    form = LoginForm(request.POST or None)

    if request.user.is_authenticated:
        return redirect("/")

    if request.method == "POST":
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")

            backend = EmailOrUsernameBackend()
            user = backend.authenticate(
                request=request, username=username, password=password
            )

            if user is not None:
                login(request, user)

                if user.is_superuser:
                    return redirect("/admin/")

                return redirect("/")
            msg = "Invalid credentials"

        else:
            msg = "Invalid Inputs"

    return render(request, "auth/login.html", {"form": form, "msg": msg})


def signup_view(request):
    msg = None
    success = False

    if request.user.is_authenticated:
        return redirect("/")

    if request.method == "POST":
        form = UserSignUpForm(request.POST)

        if form.is_valid():
            form.save()

            return redirect("login")
        msg = "Form is not valid"
    else:
        form = UserSignUpForm()

    return render(
        request,
        "auth/signup.html",
        {"form": form, "msg": msg, "success": success},
    )


@login_required()
def logout_user(request):
    logout(request)
    return redirect("/")


@login_required
@require_http_methods(["GET", "POST"])
def password_change_view(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Your password was updated successfully.")
            return redirect("my_profile")
    else:
        form = PasswordChangeForm(request.user)

    return render(request, "auth/password_change.html", {"form": form})


def _journal_streak(user):
    """Consecutive days with at least one journal entry (today or yesterday can start the chain)."""
    from journal.models import JournalEntry

    dates = set(JournalEntry.objects.filter(user=user).dates("entry_date", "day"))
    if not dates:
        return 0
    today = timezone.localdate()
    if today in dates:
        d = today
    elif today - timedelta(days=1) in dates:
        d = today - timedelta(days=1)
    else:
        return 0
    streak = 0
    while d in dates:
        streak += 1
        d -= timedelta(days=1)
    return streak


BADGE_LABELS = {
    "first_journal": "First page — you started journaling",
    "first_confession": "Brave heart — first confession",
    "first_yana": "First hug — talked to Yana",
    "first_blog_author": "Voice — authored a blog post",
}

AVATAR_EMOJI = {
    "lotus": "🪷",
    "moon": "🌙",
    "wave": "🌊",
    "mountain": "⛰️",
    "sun": "☀️",
    "leaf": "🍃",
    "heart": "💗",
    "star": "✨",
}


@login_required()
def profile_view(request):
    from blog.models import BlogBookmark, BlogPost
    from confession.models import ConfessionModal
    from journal.models import JournalEntry

    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)
    ensure_badges(user)

    journal_qs = JournalEntry.objects.filter(user=user)
    confession_qs = ConfessionModal.objects.filter(user=user)

    data = {
        "total_journal_entries": journal_qs.count(),
        "total_confessions": confession_qs.filter(is_draft=False).count(),
        "current_streak": _journal_streak(user),
        "total_blog_posts": BlogPost.objects.filter(author=user).count(),
    }

    try:
        from chatbot.models import ChatSession

        data["total_yana_chats"] = ChatSession.objects.filter(user=user).count()
    except ImportError:
        data["total_yana_chats"] = 0

    ws = week_start(timezone.localdate())
    weekly_goal, _ = UserGoal.objects.get_or_create(
        user=user,
        week_start=ws,
        defaults={"target_entries": 3, "progress": 0},
    )

    bookmarked = (
        BlogBookmark.objects.filter(user=user)
        .select_related("post")
        .order_by("-created_at")[:50]
    )

    user_confessions = (
        ConfessionModal.objects.filter(user=user)
        .order_by("-id")[:50]
    )

    recent_journals = journal_qs.order_by("-entry_date")[:15]

    badge_rows = [
        {"id": b.badge_id, "label": BADGE_LABELS.get(b.badge_id, b.badge_id)}
        for b in user.badges.all()
    ]
    avatar_choices = [
        (val, AVATAR_EMOJI.get(val, "🪷"), label)
        for val, label in UserProfile.AVATAR_CHOICES
    ]

    context = {
        "data": data,
        "profile": profile,
        "heatmap_json": json.dumps(heatmap_days(user, 35)),
        "sentiment_chart_json": json.dumps(sentiment_chart_series(user, 40)),
        "keyword_cloud": journal_keyword_cloud(user, 28),
        "monthly_insight": monthly_journal_insight(user),
        "memory_last_year": memory_this_time_last_year(user),
        "chat_recaps": chat_recaps(user),
        "user_confessions": user_confessions,
        "bookmarked_posts": bookmarked,
        "weekly_goal": weekly_goal,
        "badge_rows": badge_rows,
        "avatar_choices": avatar_choices,
        "recent_journals": recent_journals,
        "safety_plan_json": json.dumps(profile.safety_plan or {}),
        "emergency_contacts": (profile.safety_plan or {}).get("emergency_contacts")
        or [{"name": "", "phone": ""}],
        "coping_strategies": (profile.safety_plan or {}).get("coping_strategies") or [""],
    }
    return render(request, "profile.html", context)


@login_required
@require_http_methods(["POST"])
def profile_update_identity(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    profile.community_nickname = (request.POST.get("community_nickname") or "").strip()[
        :64
    ]
    av = request.POST.get("community_avatar") or "lotus"
    valid = {c[0] for c in UserProfile.AVATAR_CHOICES}
    if av in valid:
        profile.community_avatar = av
    profile.save()
    messages.success(request, "Community identity updated.")
    return redirect("my_profile")


@login_required
@require_http_methods(["POST"])
def profile_update_privacy(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    profile.default_confession_anonymous = (
        request.POST.get("default_confession_anonymous") == "on"
    )
    profile.ai_journal_analysis_consent = (
        request.POST.get("ai_journal_analysis_consent") == "on"
    )
    profile.save()
    messages.success(request, "Privacy preferences saved.")
    return redirect("my_profile")


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def profile_safety_plan_save(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    try:
        body = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)
    profile.safety_plan = body or {}
    profile.save(update_fields=["safety_plan", "updated_at"])
    return JsonResponse({"success": True})


@login_required
@require_http_methods(["POST"])
def profile_weekly_goal(request):
    ws = week_start(timezone.localdate())
    try:
        target = int(request.POST.get("target_entries") or 3)
    except ValueError:
        target = 3
    target = max(1, min(14, target))
    g, _ = UserGoal.objects.get_or_create(
        user=request.user,
        week_start=ws,
        defaults={"target_entries": target, "progress": 0},
    )
    g.target_entries = target
    g.save(update_fields=["target_entries"])
    messages.success(request, "Weekly goal updated.")
    return redirect("my_profile")


@login_required
def export_user_data(request):
    """JSON export of journals, confessions, chats, profile (not PDF)."""
    from chatbot.models import ChatMessage, ChatSession
    from confession.models import ConfessionComment, ConfessionModal
    from journal.models import JournalEntry

    user = request.user
    journals = list(
        JournalEntry.objects.filter(user=user).values(
            "id", "title", "entry", "mood", "sentiment_analysis", "entry_date"
        )
    )
    confessions = list(
        ConfessionModal.objects.filter(user=user).values(
            "id", "title", "content", "is_anonymous", "topic", "is_draft", "created_at"
        )
    )
    comments = list(
        ConfessionComment.objects.filter(user=user).values(
            "id", "confession_id", "content", "is_anonymous", "created_at"
        )
    )
    sessions = list(
        ChatSession.objects.filter(user=user).values(
            "id", "title", "topic_summary", "created_at", "updated_at"
        )
    )
    msgs = list(
        ChatMessage.objects.filter(user=user).values(
            "id", "session_id", "text", "role", "created_at"
        )
    )
    prof, _ = UserProfile.objects.get_or_create(user=user)
    payload = {
        "user": {"username": user.username, "email": user.email},
        "profile": {
            "community_nickname": prof.community_nickname,
            "default_confession_anonymous": prof.default_confession_anonymous,
            "ai_journal_analysis_consent": prof.ai_journal_analysis_consent,
            "safety_plan": prof.safety_plan,
        },
        "journal_entries": journals,
        "confessions": confessions,
        "confession_comments": comments,
        "chat_sessions": sessions,
        "chat_messages": msgs,
    }
    response = HttpResponse(
        json.dumps(payload, indent=2, default=str),
        content_type="application/json",
    )
    response["Content-Disposition"] = 'attachment; filename="soullink-my-data.json"'
    return response
