from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class ChatSession(models.Model):
    """
    Logical chat session between a user and Yana.
    Allows titling, continuing, and deleting whole chats.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="chat_sessions",
    )
    title = models.CharField(max_length=255, blank=True)
    topic_summary = models.TextField(
        blank=True,
        help_text="Short recap of themes (e.g. from Rasa actions or heuristics).",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        base = self.title or "Untitled chat"
        return f"{self.user_id} - {base}"


class ChatMessage(models.Model):
    """
    Stores individual chat messages between a user and Yana.
    """
    ROLE_USER = "user"
    ROLE_YANA = "yana"

    ROLE_CHOICES = [
        (ROLE_USER, "User"),
        (ROLE_YANA, "Yana"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_messages")
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name="messages",
        null=True,
        blank=True,
    )
    text = models.TextField()
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"{self.user_id} ({self.role}): {self.text[:40]}"
