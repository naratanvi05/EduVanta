from django.db import models
from django.conf import settings

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Announcement(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role__in': ['admin', 'teacher']}
    )
    category = models.ForeignKey('announcements.Category', on_delete=models.SET_NULL, null=True, blank=True, related_name='announcements')
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, null=True, blank=True, related_name='announcements')  # Null for global announcements
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        base = self.title or 'Announcement'
        if self.category:
            base = f"[{self.category.name}] {base}"
        return base
