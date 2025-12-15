from django.conf import settings
from django.db import models

def branding(request):
    """Inject branding variables into all templates.

    Order of precedence:
    1) SiteSetting from DB (if available)
    2) Django settings fallbacks
    """
    brand = getattr(settings, 'SITE_BRAND_NAME', 'EduVanta')
    color = getattr(settings, 'SITE_BRAND_COLOR', '#4f46e5')
    logo = getattr(settings, 'SITE_BRAND_LOGO_URL', '')
    prefix = getattr(settings, 'SITE_EMAIL_SUBJECT_PREFIX', '')

    # Try DB overrides if model exists and DB is available
    try:
        from .models import SiteSetting
        ss = SiteSetting.objects.first()
        if ss:
            brand = ss.brand_name or brand
            color = ss.brand_color or color
            logo = ss.logo_url or logo
            prefix = ss.email_subject_prefix or prefix
    except Exception:
        # Avoid failing hard if migrations not yet applied
        pass

    return {
        'brand_name': brand,
        'brand_color': color,
        'logo_url': logo,
        'email_subject_prefix': prefix,
    }


def notifications(request):
    """Inject unread notifications count and a small recent list for the header bell.

    Safe under migrations and for anonymous users.
    """
    try:
        user = getattr(request, 'user', None)
        if not getattr(user, 'is_authenticated', False):
            return {'notifications_unread_count': 0, 'notifications_recent': []}
        from .models import Notification
        unread = Notification.objects.filter(user=user, is_read=False).count()
        recent = list(Notification.objects.filter(user=user).order_by('-created_at')[:5])
        return {
            'notifications_unread_count': unread,
            'notifications_recent': recent,
        }
    except Exception:
        return {'notifications_unread_count': 0, 'notifications_recent': []}


def user_xp(request):
    """Inject total XP across all enrollments for the authenticated user."""
    try:
        user = getattr(request, 'user', None)
        if not getattr(user, 'is_authenticated', False):
            return {'user_total_xp': 0}
        from courses.models import Enrollment
        total = Enrollment.objects.filter(student=user).aggregate(models.Sum('earned_xp')).get('earned_xp__sum') or 0
        return {'user_total_xp': int(total)}
    except Exception:
        return {'user_total_xp': 0}
