from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class BlogPost(models.Model):
    CATEGORY_CHOICES = [
        ("sleep", "Sleep & rest"),
        ("mindfulness", "Mindfulness"),
        ("relationships", "Relationships"),
        ("anxiety", "Anxiety"),
        ("journaling", "Journaling"),
        ("stress", "Stress relief"),
        ("general", "General"),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, db_index=True)
    excerpt = models.TextField(max_length=500, blank=True)
    body = models.TextField()
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blog_posts",
    )
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default="general",
    )
    is_published = models.BooleanField(default=True)
    published_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at", "-id"]

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self) -> str:
        return reverse("blog_post_detail", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._unique_slug_from_title()
        super().save(*args, **kwargs)

    def _unique_slug_from_title(self) -> str:
        base = slugify(self.title)[:200] or "post"
        slug = base
        n = 1
        while (
            BlogPost.objects.filter(slug=slug).exclude(pk=self.pk).exists()
        ):
            slug = f"{base}-{n}"
            n += 1
        return slug


class BlogBookmark(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blog_bookmarks",
    )
    post = models.ForeignKey(
        BlogPost,
        on_delete=models.CASCADE,
        related_name="bookmarks",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("user", "post")]
