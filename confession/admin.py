from django.contrib import admin
from .models import ConfessionModal, ConfessionLike, ConfessionComment


@admin.register(ConfessionModal)
class ConfessionModalAdmin(admin.ModelAdmin):
    list_display = ('title', 'topic', 'user', 'is_anonymous', 'created_at')


@admin.register(ConfessionLike)
class ConfessionLikeAdmin(admin.ModelAdmin):
    list_display = ('confession', 'user', 'created_at')


@admin.register(ConfessionComment)
class ConfessionCommentAdmin(admin.ModelAdmin):
    list_display = ('confession', 'user', 'is_anonymous', 'created_at')
