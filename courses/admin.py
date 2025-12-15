from django.contrib import admin
from .models import (
    Department,
    Specialization,
    SubSpecialization,
    Course,
    CourseInstructor,
    Enrollment,
    Tag,
    Module,
    Lesson,
    CodingAssignment,
)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "order")
    search_fields = ("name", "code")
    ordering = ("order", "name")


@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = ("name", "department", "level")
    list_filter = ("department", "level")
    search_fields = ("name", "department__name", "department__code")


@admin.register(SubSpecialization)
class SubSpecializationAdmin(admin.ModelAdmin):
    list_display = ("name", "specialization", "order")
    list_filter = ("specialization",)
    search_fields = ("name", "specialization__name")


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0


class ModuleInline(admin.TabularInline):
    model = Module
    extra = 0


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "department",
        "specialization",
        "subspecialization",
        "instructor",
        "published",
        "approval_status",
        "approved_at",
    )
    list_filter = ("department", "specialization", "published", "approval_status")
    search_fields = ("title", "description")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("tags",)
    inlines = [ModuleInline]


@admin.register(CourseInstructor)
class CourseInstructorAdmin(admin.ModelAdmin):
    list_display = ("course", "instructor", "is_lead", "assigned_at")
    list_filter = ("is_lead",)
    search_fields = ("course__title", "instructor__username", "instructor__email")


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "status", "progress_percent", "grade", "created_at")
    list_filter = ("status",)
    search_fields = ("student__username", "student__email", "course__title")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ("course", "title", "order")
    list_filter = ("course",)
    search_fields = ("title", "course__title")


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("module", "title", "order")
    list_filter = ("module__course",)
    search_fields = ("title", "module__title", "module__course__title")


@admin.register(CodingAssignment)
class CodingAssignmentAdmin(admin.ModelAdmin):
    list_display = ("lesson", "language", "auto_grade", "time_limit_ms")
    list_filter = ("language", "auto_grade")
    search_fields = ("lesson__title",)
