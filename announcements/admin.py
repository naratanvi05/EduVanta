from django.contrib import admin
from .models import Announcement, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "slug")
    list_display = ("name", "slug")


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "posted_by", "created_at")
    list_filter = ("category", "created_at")
    search_fields = ("title", "content")
    autocomplete_fields = ("category", "posted_by", "course")
