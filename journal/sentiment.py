"""
Keyword and sentiment helpers for journals (used by chatbot and profile insights).
"""

from __future__ import annotations

import re
from collections import Counter

# Minimal English stopwords for keyword clouds
_STOPWORDS = frozenset(
    """
    a an the and or but if in on at to for of as is was were be been being
    have has had do does did will would could should may might must can
    i me my we our you your he she it they them their this that these those
    what which who when where why how not no yes so than then too very just
    also only even about into through over after before with from up down out
    off am here there some any all both each few more most other such same
    than into onto by
    """.split()
)


def extract_emotional_state(text: str) -> dict:
    """
    Extract emotional state from journal text using keyword analysis.
    """
    text_lower = text.lower()

    positive_keywords = [
        "happy",
        "joy",
        "joyful",
        "grateful",
        "thankful",
        "excited",
        "proud",
        "content",
        "peaceful",
        "calm",
        "hopeful",
        "optimistic",
        "love",
        "appreciate",
        "blessed",
        "relieved",
        "motivated",
        "inspired",
        "confident",
        "energized",
        "fulfilled",
        "satisfied",
        "cheerful",
        "delighted",
        "wonderful",
        "amazing",
        "great",
        "good",
        "better",
        "improved",
        "progress",
        "accomplish",
        "success",
    ]
    negative_keywords = [
        "sad",
        "depressed",
        "anxious",
        "worried",
        "stressed",
        "angry",
        "frustrated",
        "overwhelmed",
        "lonely",
        "hurt",
        "disappointed",
        "fear",
        "scared",
        "afraid",
        "hopeless",
        "helpless",
        "exhausted",
        "tired",
        "drained",
        "empty",
        "numb",
        "guilty",
        "ashamed",
        "embarrassed",
        "rejected",
        "abandoned",
        "isolated",
        "confused",
        "lost",
        "stuck",
        "trapped",
        "panic",
        "dread",
        "despair",
        "irritable",
        "resentful",
        "bitter",
        "jealous",
        "envious",
        "inadequate",
    ]
    neutral_keywords = [
        "okay",
        "fine",
        "normal",
        "alright",
        "neutral",
        "average",
        "same",
        "routine",
    ]

    positive_count = sum(1 for word in positive_keywords if word in text_lower)
    negative_count = sum(1 for word in negative_keywords if word in text_lower)
    neutral_count = sum(1 for word in neutral_keywords if word in text_lower)

    total = positive_count + negative_count + neutral_count
    if total == 0:
        state = "mixed"
        confidence = 0.3
    elif positive_count > negative_count and positive_count > 0:
        state = "positive"
        confidence = min(positive_count / (total + 1), 0.95)
    elif negative_count > positive_count and negative_count > 0:
        state = "negative"
        confidence = min(negative_count / (total + 1), 0.95)
    elif neutral_count > 0 and positive_count == 0 and negative_count == 0:
        state = "neutral"
        confidence = 0.5
    else:
        state = "mixed"
        confidence = min(max(positive_count, negative_count) / (total + 1), 0.7)

    return {
        "state": state,
        "confidence": round(confidence, 2),
        "positive_indicators": positive_count,
        "negative_indicators": negative_count,
    }


def sentiment_to_chart_score(analysis: dict | None) -> float | None:  # noqa: UP007
    if not analysis:
        return None
    state = analysis.get("state")
    conf = float(analysis.get("confidence") or 0.5)
    base = {"positive": 1.0, "neutral": 0.0, "negative": -1.0, "mixed": 0.0}.get(
        state, 0.0
    )
    return round(base * conf, 3)


def keyword_frequencies(text: str, top_n: int = 25) -> list[tuple[str, int]]:
    words = re.findall(r"[a-zA-Z]{3,}", text.lower())
    words = [w for w in words if w not in _STOPWORDS]
    return Counter(words).most_common(top_n)


def build_monthly_summary(entries, top_keywords: list[tuple[str, int]]) -> str | None:
    if not entries:
        return None
    parts = []
    if top_keywords:
        w, _ = top_keywords[0]
        parts.append(f'You wrote often about "{w}" this month.')
    moods = [getattr(e, "mood", None) for e in entries]
    from collections import Counter as C

    mc = C(m for m in moods if m)
    if mc:
        common, _ = mc.most_common(1)[0]
        parts.append(f"Your most-selected mood was {common.replace('_', ' ')}.")
    pos_days = sum(
        1
        for e in entries
        if e.sentiment_analysis
        and e.sentiment_analysis.get("state") == "positive"
    )
    if pos_days >= len(entries) // 2 and len(entries) >= 2:
        parts.append(
            "Several entries leaned positive—notice what was different on those days."
        )
    return " ".join(parts) if parts else None
