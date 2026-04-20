"""
Keyword and sentiment helpers for journals (used by chatbot and profile insights).
"""

from __future__ import annotations

import re
from collections import Counter
from math import exp

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


_NEGATIONS = frozenset(
    {
        "not",
        "no",
        "never",
        "none",
        "nothing",
        "hardly",
        "barely",
        "dont",
        "don't",
        "didnt",
        "didn't",
        "cant",
        "can't",
        "wont",
        "won't",
    }
)

_INTENSIFIERS = frozenset(
    {
        "very",
        "really",
        "so",
        "extremely",
        "incredibly",
        "super",
        "quite",
        "too",
    }
)


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + exp(-x))


def _tokenize(text: str) -> list[str]:
    # Keep simple word tokens; also normalize common apostrophe removals.
    s = (text or "").lower()
    s = s.replace("’", "'")
    return re.findall(r"[a-z']+", s)


def extract_emotional_state(text: str) -> dict:
    """
    Extract emotional state from journal text using keyword analysis.
    """
    tokens = _tokenize(text)
    text_lower = " ".join(tokens)

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

    # Count occurrences with simple negation/intensifier handling.
    # We treat a keyword as "hit" if it appears as a token or phrase in the text.
    # For single-word keywords, we count token occurrences; for phrases, substring match.
    token_counts = Counter(tokens)

    def phrase_hits(phrases: list[str]) -> int:
        hits = 0
        for p in phrases:
            p = p.lower()
            if " " in p:
                if p in text_lower:
                    hits += 1
            else:
                hits += int(token_counts.get(p, 0))
        return hits

    raw_pos = phrase_hits(positive_keywords)
    raw_neg = phrase_hits(negative_keywords)
    raw_neu = phrase_hits(neutral_keywords)

    # Adjust for local negation around emotional words (e.g., "not happy").
    # Window of 3 tokens back.
    pos_adjust = 0
    neg_adjust = 0
    for i, tok in enumerate(tokens):
        if tok in token_counts:
            window = tokens[max(0, i - 3) : i]
            has_neg = any(w in _NEGATIONS for w in window)
            has_int = any(w in _INTENSIFIERS for w in window)
            if has_int:
                # Intensifiers increase evidence strength.
                if tok in positive_keywords:
                    pos_adjust += 1
                if tok in negative_keywords:
                    neg_adjust += 1
            if has_neg:
                # Negation flips a bit of evidence.
                if tok in positive_keywords:
                    raw_pos = max(0, raw_pos - 1)
                    raw_neg += 1
                elif tok in negative_keywords:
                    raw_neg = max(0, raw_neg - 1)
                    raw_pos += 1

    positive_count = max(0, raw_pos + pos_adjust)
    negative_count = max(0, raw_neg + neg_adjust)
    neutral_count = max(0, raw_neu)

    total = positive_count + negative_count + neutral_count

    if total == 0:
        # No evidence; keep it cautious.
        state = "mixed"
        confidence = 0.25
    else:
        if positive_count == 0 and negative_count == 0 and neutral_count > 0:
            state = "neutral"
        elif positive_count > negative_count:
            state = "positive"
        elif negative_count > positive_count:
            state = "negative"
        else:
            state = "mixed"

        # Confidence is a product of:
        # - evidence strength (more indicators => higher)
        # - clarity (margin between pos and neg)
        evidence_strength = _sigmoid((total - 2) / 2.0)  # ramps up after ~2 hits
        if positive_count + negative_count == 0:
            clarity = 0.6  # neutral-only evidence is inherently less specific
        else:
            margin = abs(positive_count - negative_count)
            clarity = min(1.0, 0.55 + 0.15 * margin)

        # Slight downweight when mixed signals dominate.
        mixed_penalty = 1.0
        if state == "mixed" and positive_count + negative_count > 0:
            mixed_penalty = 0.85

        confidence = min(0.97, max(0.05, evidence_strength * clarity * mixed_penalty))

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
