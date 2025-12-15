from django.contrib import admin
from .models import Challenge, ChallengeParticipation, Streak

@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ("title", "xp_reward", "start_at", "end_at", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title", "description", "slug")
    prepopulated_fields = {"slug": ("title",)}

@admin.register(ChallengeParticipation)
class ChallengeParticipationAdmin(admin.ModelAdmin):
    list_display = ("student", "challenge", "status", "awarded_xp", "completed_at")
    list_filter = ("status",)
    search_fields = ("student__username", "challenge__title")

@admin.register(Streak)
class StreakAdmin(admin.ModelAdmin):
    list_display = ("student", "count", "longest", "last_activity_date")
    search_fields = ("student__username",)
