from django.db import models
from accounts.models import CustomUser


class ConfessionModal(models.Model):
    TOPIC_CHOICE = [
        ("STRESS", "Stress"),
        ("ANXIETY", "Anxiety"),
        ("DEPRESSION", "Depression"),
        ("RELATIONSHIP", "Relationship Issues"),
        ("OTHERS", "Others"),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    content = models.CharField(max_length=5000)
    is_anonymous = models.BooleanField(default=True)
    topic = models.CharField(
        max_length=50, choices=TOPIC_CHOICE, default="OTHERS", blank=False
    )
    created_at = models.DateTimeField(auto_now=True)

    @property
    def like_count(self):
        return self.likes.count()

    @property
    def comment_count(self):
        return self.comments.count()


class ConfessionLike(models.Model):
    """Like on a confession post."""
    confession = models.ForeignKey(
        ConfessionModal, on_delete=models.CASCADE, related_name="likes"
    )
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("confession", "user")


class ConfessionComment(models.Model):
    """Comment on a confession post."""
    confession = models.ForeignKey(
        ConfessionModal, on_delete=models.CASCADE, related_name="comments"
    )
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content = models.CharField(max_length=1000)
    is_anonymous = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
