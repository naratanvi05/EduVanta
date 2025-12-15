from __future__ import annotations
from datetime import date, timedelta
from django.utils.deprecation import MiddlewareMixin
from django.db import transaction

try:
    from .models import Streak
except Exception:  # during migrations
    Streak = None  # type: ignore


class StreakMiddleware(MiddlewareMixin):
    """Lightweight middleware to maintain daily learning streaks for students.

    Logic:
    - Only for authenticated users with role == 'student'.
    - Creates a Streak row on first encounter.
    - If last_activity_date == today       -> do nothing
    - If last_activity_date == yesterday   -> increment count
    - Else                                 -> reset count to 1
    - Update longest when count exceeds previous best.

    Keep it very cheap per-request. We avoid heavy locks and only touch the DB
    when the date actually changes for the student.
    """

    def process_request(self, request):
        user = getattr(request, 'user', None)
        if not getattr(user, 'is_authenticated', False):
            return None
        if getattr(user, 'role', None) != 'student':
            return None
        if Streak is None:
            return None
        today = date.today()
        try:
            # Fetch without creating when not needed; create lazily when missing
            streak = getattr(user, 'streak', None)
            if streak is None:
                with transaction.atomic():
                    streak, _ = Streak.objects.get_or_create(student=user, defaults={
                        'last_activity_date': today,
                        'count': 1,
                        'longest': 1,
                    })
                # attach for this request lifetime
                try:
                    setattr(user, 'streak', streak)
                except Exception:
                    pass
                return None
            # If already updated today, skip
            if streak.last_activity_date == today:
                return None
            # Update based on gap
            if streak.last_activity_date == today - timedelta(days=1):
                streak.count = int(streak.count or 0) + 1
            else:
                streak.count = 1
            streak.last_activity_date = today
            if int(streak.count or 0) > int(streak.longest or 0):
                streak.longest = streak.count
            streak.save(update_fields=['last_activity_date', 'count', 'longest'])
        except Exception:
            # Never block requests due to streak bookkeeping
            return None
        return None
