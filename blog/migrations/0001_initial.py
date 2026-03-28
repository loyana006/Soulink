import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="BlogPost",
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
                ("title", models.CharField(max_length=200)),
                ("slug", models.SlugField(max_length=220, unique=True)),
                ("excerpt", models.TextField(blank=True, max_length=500)),
                ("body", models.TextField()),
                (
                    "category",
                    models.CharField(
                        choices=[
                            ("sleep", "Sleep & rest"),
                            ("mindfulness", "Mindfulness"),
                            ("relationships", "Relationships"),
                            ("anxiety", "Anxiety"),
                            ("journaling", "Journaling"),
                            ("stress", "Stress relief"),
                            ("general", "General"),
                        ],
                        default="general",
                        max_length=50,
                    ),
                ),
                ("is_published", models.BooleanField(default=True)),
                (
                    "published_at",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "author",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="blog_posts",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-published_at", "-id"],
            },
        ),
    ]
