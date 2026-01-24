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
