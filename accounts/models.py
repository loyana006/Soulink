from datetime import date

from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    dob = models.DateField(blank=False, default=date(1111, 1, 1))
    address = models.TextField(blank=True, null=True, max_length=50, default="")
    password = models.CharField(max_length=255)

    def __str__(self):
        return self.username

    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class UserProfile(models.Model):
    """
    Community identity, privacy preferences, and safety plan (stored as structured JSON).
    """

    AVATAR_CHOICES = [
        ("lotus", "Lotus"),
        ("moon", "Moon"),
        ("wave", "Wave"),
        ("mountain", "Mountain"),
        ("sun", "Sun"),
        ("leaf", "Leaf"),
        ("heart", "Heart"),
        ("star", "Star"),
    ]

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    community_nickname = models.CharField(
        max_length=64,
        blank=True,
        help_text="Shown on confessionals when not anonymous (optional).",
    )
    community_avatar = models.CharField(
        max_length=16,
        choices=AVATAR_CHOICES,
        default="lotus",
    )
    default_confession_anonymous = models.BooleanField(
        default=True,
        help_text="Default for new confession posts.",
    )
    ai_journal_analysis_consent = models.BooleanField(
        default=True,
        help_text="Allow keyword-based sentiment to be stored on journal entries.",
    )
    safety_plan = models.JSONField(
        default=dict,
        blank=True,
        help_text='{"emergency_contacts":[{"name":"","phone":""}],"coping_strategies":[""]}',
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Profile({self.user_id})"

    def avatar_emoji(self) -> str:
        m = {
            "lotus": "🪷",
            "moon": "🌙",
            "wave": "🌊",
            "mountain": "⛰️",
            "sun": "☀️",
            "leaf": "🍃",
            "heart": "💗",
            "star": "✨",
        }
        return m.get(self.community_avatar, "🪷")

    def community_display_name(self) -> str:
        return (self.community_nickname or "").strip() or self.user.username


class UserGoal(models.Model):
    """Simple weekly journaling goal."""

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="weekly_goals",
    )
    week_start = models.DateField()
    target_entries = models.PositiveSmallIntegerField(default=3)
    progress = models.PositiveSmallIntegerField(default=0)

    class Meta:
        unique_together = [("user", "week_start")]

    def __str__(self) -> str:
        return f"{self.user_id} week {self.week_start}"


class UserBadge(models.Model):
    """Non-clinical milestones."""

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="badges",
    )
    badge_id = models.CharField(max_length=40)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("user", "badge_id")]

    def __str__(self) -> str:
        return f"{self.user_id} {self.badge_id}"
