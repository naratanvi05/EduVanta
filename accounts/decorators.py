from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse


def role_required(*allowed_roles):
    """
    Decorator to restrict a view to users with certain roles.
    Usage:
        @login_required
        @role_required('student')
        def student_view(...):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            user = getattr(request, 'user', None)
            role = getattr(user, 'role', None)
            if not user or not user.is_authenticated:
                return redirect(f"{reverse('accounts:login')}?next={request.path}")
            if allowed_roles and role not in allowed_roles:
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('accounts:dashboard')
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator
