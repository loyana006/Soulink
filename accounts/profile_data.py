"""
Aggregates dashboard data for the profile hub (insights, heatmap, summaries).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

from django.utils import timezone

from journal.models import JournalEntry
from journal.sentiment import (
    build_monthly_summary,
    keyword_frequencies,
    sentiment_to_chart_score,
)


def week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


def mood_level(mood: str) -> int:
    return {
        "great": 5,
        "good": 4,
        "okay": 3,
        "low": 2,
        "tough": 1,
        "": 0,
    }.get(mood or "", 0)


def heatmap_days(user, days: int = 35) -> list[dict]:
    """Last `days` calendar days: {date, level 0–5, has_entry}."""
    today = timezone.localdate()
    start = today - timedelta(days=days - 1)
    start_dt = timezone.make_aware(datetime.combine(start, datetime.min.time()))
    entries = JournalEntry.objects.filter(
        user=user, entry_date__gte=start_dt
    ).only("entry_date", "mood", "sentiment_analysis")
    by_date: dict[date, JournalEntry] = {}
    for e in entries:
        d = timezone.localtime(e.entry_date).date()
        if d not in by_date or e.entry_date > by_date[d].entry_date:
            by_date[d] = e

    out = []
    for i in range(days):
        d = start + timedelta(days=i)
        e = by_date.get(d)
        if e:
            lvl = mood_level(e.mood)
            if not e.mood and e.sentiment_analysis:
                st = e.sentiment_analysis.get("state")
                lvl = {"positive": 4, "neutral": 3, "negative": 2, "mixed": 3}.get(
                    st, 2
                )
        else:
            lvl = 0
        out.append({"date": d.isoformat(), "level": lvl, "has_entry": e is not None})
    return out


def sentiment_chart_series(user, limit: int = 40) -> list[dict]:
    qs = (
        JournalEntry.objects.filter(user=user)
        .exclude(sentiment_analysis__isnull=True)
        .order_by("-entry_date")[:limit]
    )
    series = []
    for e in reversed(list(qs)):
        sa = e.sentiment_analysis or {}
        score = sentiment_to_chart_score(sa)
        if score is None:
            continue
        series.append(
            {
                "t": timezone.localtime(e.entry_date).strftime("%Y-%m-%d"),
                "score": score,
                "state": sa.get("state"),
            }
        )
    return series


def journal_keyword_cloud(user, top_n: int = 30) -> list[tuple[str, int]]:
    qs = JournalEntry.objects.filter(user=user).only("title", "entry")[:200]
    blob = " ".join(f"{e.title} {e.entry}" for e in qs)
    if not blob.strip():
        return []
    return keyword_frequencies(blob, top_n=top_n)


def monthly_journal_insight(user) -> str | None:
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    entries = list(
        JournalEntry.objects.filter(user=user, entry_date__gte=month_start).order_by(
            "-entry_date"
        )
    )
    if not entries:
        return None
    blob = " ".join(f"{e.title} {e.entry}" for e in entries)
    kw = keyword_frequencies(blob, top_n=5) if blob.strip() else []
    return build_monthly_summary(entries, kw)


def memory_this_time_last_year(user):
    today = timezone.localdate()
    try:
        target = date(today.year - 1, today.month, today.day)
    except ValueError:
        return None
    start = timezone.make_aware(datetime.combine(target, datetime.min.time()))
    end = timezone.make_aware(datetime.combine(target, datetime.max.time()))
    e = (
        JournalEntry.objects.filter(user=user, entry_date__range=(start, end))
        .order_by("-entry_date")
        .first()
    )
    if not e:
        return None
    return {
        "title": e.title,
        "snippet": (e.entry or "")[:280],
        "mood": e.mood,
        "date": target.isoformat(),
    }


def chat_recaps(user, limit: int = 5):
    try:
        from chatbot.models import ChatSession

        qs = (
            ChatSession.objects.filter(user=user)
            .exclude(topic_summary="")
            .order_by("-updated_at")[:limit]
        )
        return [
            {"title": s.title or "Chat", "summary": s.topic_summary, "id": s.id}
            for s in qs
        ]
    except ImportError:
        return []


def ensure_badges(user):
    """Award milestone badges idempotently."""
    from accounts.models import UserBadge
    from blog.models import BlogPost
    from chatbot.models import ChatSession
    from confession.models import ConfessionModal

    checks = []
    if JournalEntry.objects.filter(user=user).exists():
        checks.append("first_journal")
    if ConfessionModal.objects.filter(user=user, is_draft=False).exists():
        checks.append("first_confession")
    if ChatSession.objects.filter(user=user).exists():
        checks.append("first_yana")
    if BlogPost.objects.filter(author=user).exists():
        checks.append("first_blog_author")

    for bid in checks:
        UserBadge.objects.get_or_create(user=user, badge_id=bid)
