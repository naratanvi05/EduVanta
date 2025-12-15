from django.db import models
from django.conf import settings
from django.utils import timezone


class Challenge(models.Model):
    """Dynamic challenges that award bonus XP when completed within a window.
    Dormant: app not added to INSTALLED_APPS yet.
    """
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    xp_reward = models.PositiveIntegerField(default=50)
    start_at = models.DateTimeField(null=True, blank=True)
    end_at = models.DateTimeField(null=True, blank=True)
    slug = models.SlugField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    # Workflow/ownership
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="challenges_created")
    is_approved = models.BooleanField(default=False, help_text="Approved challenges are visible to students.")
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class ChallengeParticipation(models.Model):
    PENDING = "pending"
    COMPLETED = "completed"
    STATUS_CHOICES = (
        (PENDING, "Pending"),
        (COMPLETED, "Completed"),
    )
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="challenge_participations")
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name="participations")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=PENDING)
    completed_at = models.DateTimeField(null=True, blank=True)
    awarded_xp = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "challenge")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.student} - {self.challenge} ({self.status})"


class Streak(models.Model):
    """Tracks daily learning streaks for XP multipliers."""
    student = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="streak")
    last_activity_date = models.DateField(null=True, blank=True)
    count = models.PositiveIntegerField(default=0)
    longest = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student} streak {self.count} (best {self.longest})"


class DailyActivity(models.Model):
    """Normalized record of daily learning actions to support accurate streaks and analytics.
    One row per user per day. The counter may be incremented multiple times a day; presence = activity.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="daily_activities")
    date = models.DateField()
    count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "date")
        ordering = ["-date", "-updated_at"]

    def __str__(self):
        return f"Activity {self.user} @ {self.date} x{self.count}"


def record_daily_activity(user, when=None):
    """Upsert a DailyActivity row and update/create Streak for the user.
    This can be called by other apps when a meaningful learning action occurs.
    """
    if not user or not getattr(user, 'id', None):
        return
    when = when or timezone.now()
    day = when.date()
    # Upsert activity
    obj, _ = DailyActivity.objects.get_or_create(user=user, date=day, defaults={"count": 0})
    try:
        obj.count = int(obj.count or 0) + 1
        obj.save(update_fields=["count", "updated_at"])
    except Exception:
        # tolerate race conditions in dev
        pass
    # Update streak
    st, _ = Streak.objects.get_or_create(student=user)
    last = st.last_activity_date
    if last == day:
        # already counted today; leave as-is
        st.updated_at = timezone.now()
        st.save(update_fields=["updated_at"])
        return
    if last is None:
        st.count = 1
    else:
        # If activity happened yesterday, increase; else reset
        if (day - last).days == 1:
            st.count = int(st.count or 0) + 1
        elif (day - last).days >= 0:
            st.count = 1
        else:
            # future anomaly; reset
            st.count = 1
    if st.count > (st.longest or 0):
        st.longest = st.count
    st.last_activity_date = day
    st.save()
