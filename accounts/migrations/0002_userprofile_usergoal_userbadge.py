import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def create_profiles(apps, schema_editor):
    User = apps.get_model("accounts", "CustomUser")
    UserProfile = apps.get_model("accounts", "UserProfile")
    for u in User.objects.all():
        UserProfile.objects.get_or_create(user_id=u.pk)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserProfile",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "community_nickname",
                    models.CharField(
                        blank=True,
                        help_text="Shown on confessionals when not anonymous (optional).",
                        max_length=64,
                    ),
                ),
                (
                    "community_avatar",
                    models.CharField(
                        choices=[
                            ("lotus", "Lotus"),
                            ("moon", "Moon"),
                            ("wave", "Wave"),
                            ("mountain", "Mountain"),
                            ("sun", "Sun"),
                            ("leaf", "Leaf"),
                            ("heart", "Heart"),
                            ("star", "Star"),
                        ],
                        default="lotus",
                        max_length=16,
                    ),
                ),
                (
                    "default_confession_anonymous",
                    models.BooleanField(
                        default=True,
                        help_text="Default for new confession posts.",
                    ),
                ),
                (
                    "ai_journal_analysis_consent",
                    models.BooleanField(
                        default=True,
                        help_text="Allow keyword-based sentiment to be stored on journal entries.",
                    ),
                ),
                ("safety_plan", models.JSONField(blank=True, default=dict)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="profile",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="UserBadge",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("badge_id", models.CharField(max_length=40)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="badges",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "unique_together": {("user", "badge_id")},
            },
        ),
        migrations.CreateModel(
            name="UserGoal",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("week_start", models.DateField()),
                ("target_entries", models.PositiveSmallIntegerField(default=3)),
                ("progress", models.PositiveSmallIntegerField(default=0)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="weekly_goals",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "unique_together": {("user", "week_start")},
            },
        ),
        migrations.RunPython(create_profiles, noop_reverse),
    ]
