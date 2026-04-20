from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods


def index(request):
    return render(request, "index.html")


def about(request):
    return render(request, "about.html")


def support(request):
    return render(request, "support.html")


def chatbot(request):
    active_session = None
    initial_messages = []

    if request.user.is_authenticated:
        try:
            from chatbot.models import ChatSession

            session_pk = request.session.get("yana_session_pk")
            if session_pk:
                active_session = (
                    ChatSession.objects.filter(id=session_pk, user=request.user)
                    .prefetch_related("messages")
                    .first()
                )
            if active_session:
                initial_messages = list(active_session.messages.all())
        except Exception:
            # If the chatbot app isn't available or db isn't ready, degrade gracefully.
            active_session = None
            initial_messages = []

    return render(
        request,
        "yana.html",
        {"active_session": active_session, "initial_messages": initial_messages},
    )


def dashboard(request):
    from blog.models import BlogPost
    from journal.models import JournalEntry

    recent_blog_posts = BlogPost.objects.filter(is_published=True).order_by(
        "-published_at"
    )[:3]
    if not request.user.is_authenticated:
        return render(
            request,
            "dashboard.html",
            {
                "recent_blog_posts": recent_blog_posts,
                "snapshot": {
                    "journals_last_7": 0,
                    "most_frequent_mood": "No data yet",
                    "days_streak": 0,
                },
                "chart_points": [],
            },
        )

    today = timezone.localdate()
    start_7 = today - timedelta(days=6)
    journal_qs = JournalEntry.objects.filter(user=request.user)

    journals_last_7 = journal_qs.filter(
        entry_date__date__gte=start_7,
        entry_date__date__lte=today,
    ).count()

    mood_counts = {}
    for mood in journal_qs.values_list("mood", flat=True):
        if not mood:
            continue
        mood_counts[mood] = mood_counts.get(mood, 0) + 1
    mood_labels = dict(JournalEntry.MOOD_CHOICES)
    if mood_counts:
        top_mood = max(mood_counts, key=mood_counts.get)
        most_frequent_mood = mood_labels.get(top_mood, top_mood.title())
    else:
        most_frequent_mood = "No data yet"

    dates = set(journal_qs.dates("entry_date", "day"))
    if today in dates:
        d = today
    elif (today - timedelta(days=1)) in dates:
        d = today - timedelta(days=1)
    else:
        d = None
    streak = 0
    while d and d in dates:
        streak += 1
        d -= timedelta(days=1)

    mood_score = {"great": 5, "good": 4, "okay": 3, "low": 2, "tough": 1}
    chart_points = []
    by_day = {}
    for e in journal_qs.filter(entry_date__date__gte=start_7).only("entry_date", "mood"):
        day = timezone.localtime(e.entry_date).date()
        by_day.setdefault(day, []).append(e)
    for i in range(7):
        day = start_7 + timedelta(days=i)
        entries = by_day.get(day, [])
        if entries:
            scores = [mood_score.get(e.mood, 3) for e in entries]
            avg_score = round(sum(scores) / len(scores), 2)
        else:
            avg_score = 0
        chart_points.append(
            {
                "label": day.strftime("%a"),
                "score": avg_score,
                "entries": len(entries),
            }
        )

    # Mood distribution for the same 7-day window
    week_entries = journal_qs.filter(
        entry_date__date__gte=start_7, entry_date__date__lte=today
    ).only("mood")
    dist = {"great": 0, "good": 0, "okay": 0, "low": 0, "tough": 0, "": 0}
    for mood in week_entries.values_list("mood", flat=True):
        dist[mood or ""] = dist.get(mood or "", 0) + 1
    week_total = sum(v for k, v in dist.items() if k)
    mood_colors = {
        "great": "#ff69b4",
        "good": "#20c997",
        "okay": "#0dcaf0",
        "low": "#ffc107",
        "tough": "#dc3545",
    }
    week_mood_dist = []
    for key in ["great", "good", "okay", "low", "tough"]:
        cnt = dist.get(key, 0)
        pct = round((cnt / week_total) * 100, 1) if week_total else 0
        week_mood_dist.append(
            {
                "key": key,
                "label": mood_labels.get(key, key.title()),
                "count": cnt,
                "pct": pct,
                "color": mood_colors.get(key, "#6c757d"),
            }
        )

    # SVG line chart coordinates (viewBox 0 0 320 140)
    svg_w = 320
    svg_h = 140
    pad = 16
    plot_w = svg_w - pad * 2
    plot_h = 96
    xs = [pad + (plot_w * i / 6) for i in range(7)]
    svg_points = []
    for idx, p in enumerate(chart_points):
        score = float(p["score"] or 0)
        if score <= 0:
            y = pad + plot_h
        else:
            y = pad + (1 - (score / 5.0)) * plot_h
        svg_points.append(
            {
                **p,
                "x": round(xs[idx], 2),
                "y": round(y, 2),
                "has_data": score > 0,
            }
        )
    svg_polyline = " ".join(f'{p["x"]},{p["y"]}' for p in svg_points)

    return render(
        request,
        "dashboard.html",
        {
            "recent_blog_posts": recent_blog_posts,
            "snapshot": {
                "journals_last_7": journals_last_7,
                "most_frequent_mood": most_frequent_mood,
                "days_streak": streak,
            },
            "chart_points": chart_points,
            "week_mood_dist": week_mood_dist,
            "svg_points": svg_points,
            "svg_polyline": svg_polyline,
        },
    )


@login_required
@require_http_methods(["POST"])
def quick_journal(request):
    from journal.models import JournalEntry

    raw_entry = (request.POST.get("quick_entry") or "").strip()
    if not raw_entry:
        messages.error(request, "Quick thought cannot be empty.")
        return redirect("dashboard")
    JournalEntry.objects.create(
        user=request.user,
        title="Quick thought",
        entry=raw_entry[:50000],
    )
    messages.success(request, "Quick thought saved to your journal.")
    return redirect("journal")
