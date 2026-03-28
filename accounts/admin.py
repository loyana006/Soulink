from django.contrib import admin

from .models import UserBadge, UserGoal, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "community_nickname", "default_confession_anonymous", "ai_journal_analysis_consent")


@admin.register(UserGoal)
class UserGoalAdmin(admin.ModelAdmin):
    list_display = ("user", "week_start", "target_entries", "progress")


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ("user", "badge_id", "created_at")
