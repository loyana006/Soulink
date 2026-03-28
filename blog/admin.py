from django.contrib import admin

from .models import BlogBookmark, BlogPost


@admin.register(BlogBookmark)
class BlogBookmarkAdmin(admin.ModelAdmin):
    list_display = ("user", "post", "created_at")


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "author",
        "is_published",
        "published_at",
    )
    list_filter = ("is_published", "category")
    search_fields = ("title", "body", "excerpt")
    prepopulated_fields = {"slug": ("title",)}
    raw_id_fields = ("author",)
    date_hierarchy = "published_at"
