from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from django.contrib import messages
import logging

SAFE_PREFIXES = (
    '/admin',
    '/static',
    '/media',
)
SAFE_ALWAYS = {
    # Profile-setup flow and supporting endpoints
    'accounts:profile_setup',
    'accounts:profile_setup_save',
    'accounts:profile_setup_complete',
    'accounts:remind_later',
    # OTP / auth utilities
    'accounts:verify_otp',
    'accounts:resend_otp',
    'accounts:logout',
    # Password reset routes (root and namespaced aliases)
    'accounts:password_reset',
    'accounts:password_reset_done',
    'accounts:password_reset_confirm',
    'accounts:password_reset_complete',
    'password_reset_confirm',
    # Parent flow
    'accounts:parent_link_children',
}

# Public-only routes (allowed for anonymous users; when authenticated and profile
# is incomplete, we still enforce redirect from these)
SAFE_PUBLIC = {
    'home',
    'accounts:login',
    'accounts:register',
}

class ProfileSetupRedirectMiddleware(MiddlewareMixin):
    """Redirect authenticated users to profile setup if not completed yet.
    Skips admin, static/media, OTP verification, login/logout, and the wizard itself.
    """
    def process_request(self, request):
        logger = logging.getLogger(__name__)
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return None

        # Allow safe prefixes (admin, static, media)
        path = request.path or ''
        if any(path.startswith(p) for p in SAFE_PREFIXES):
            return None

        # Allow safe named URLs
        try:
            resolved_name = request.resolver_match.view_name if request.resolver_match else None
        except Exception:
            resolved_name = None
        # Allow public routes only for anonymous users
        if resolved_name in SAFE_PUBLIC:
            # If user is anonymous, allow
            # (We are in authenticated block, so user is logged in) -> do not allow here
            pass
        # Always-allowed routes for authenticated users
        if resolved_name in SAFE_ALWAYS:
            return None

        # Skip API endpoints so AJAX/mobile clients can function
        if path.startswith('/courses/api/') or path.startswith('/api/'):
            return None
        # Allow social auth endpoints
        if path.startswith('/social-auth/'):
            return None

        # Enforce OTP verification for normal users.
        # Allow admin/staff to proceed without OTP.
        if (
            hasattr(user, 'is_verified')
            and not user.is_verified
            and not (getattr(user, 'role', None) == 'admin' or getattr(user, 'is_staff', False))
        ):
            try:
                logger.debug('Redirecting to verify_otp: user=%s path=%s reason=is_verified_false', getattr(user, 'id', None), request.path)
            except Exception:
                pass
            return redirect(reverse('accounts:verify_otp'))

        # Now prevent self-redirect loops: if we're already on profile-setup (or alias), allow
        if path.startswith('/accounts/profile-setup/') or path == '/accounts/profile-setup/':
            return None
        if path.startswith('/auth/profile-setup/') or path == '/auth/profile-setup/':
            return None

        # Allow ONE request after Skip (except to profile-setup) once user is verified
        allow_once = bool(request.session.get('allow_dashboard_once', False))
        if allow_once and getattr(user, 'is_verified', False):
            # Do not allow if user is explicitly opening profile-setup again
            if not (path.startswith('/accounts/profile-setup/') or path == '/accounts/profile-setup/'):
                try:
                    request.session.pop('allow_dashboard_once', None)
                    messages.info(request, 'You skipped the setup once. Please complete your profile to personalize your experience. Go to Profile Setup from the banner or menu.')
                    request.session['show_profile_setup_banner'] = True
                except Exception:
                    pass
                return None

        # Profile setup: do NOT force-redirect; show a banner if incomplete, but allow dashboard access
        role = getattr(user, 'role', None)
        profile_incomplete = False
        if role in ('student', 'teacher'):
            if hasattr(user, 'is_profile_completed'):
                profile_incomplete = not bool(user.is_profile_completed)
        elif role == 'parent':
            try:
                from accounts.models import ParentChildLink
                has_child = ParentChildLink.objects.filter(parent=user).exists()
            except Exception:
                has_child = False
            # Incomplete if profile flag is false OR if no child link exists
            if hasattr(user, 'is_profile_completed'):
                profile_incomplete = (not bool(user.is_profile_completed)) or (not has_child)
            else:
                profile_incomplete = not has_child

        if profile_incomplete:
            try:
                request.session['show_profile_setup_banner'] = True
            except Exception:
                pass

        # Role-based dashboard redirect for generic entry points (home/login/register root)
        # Avoid redirect loops: do not redirect from SAFE_ALWAYS or API/static/admin.
        try:
            resolved_name = request.resolver_match.view_name if request.resolver_match else None
        except Exception:
            resolved_name = None

        def reverse_safely(name):
            try:
                return reverse(name)
            except Exception:
                return None

        # Compute target dashboard based on role
        target_url = None
        if role == 'admin':
            target_url = '/admin/'
        elif role == 'student':
            for nm in ('students:dashboard', 'student:dashboard', 'accounts:student_dashboard', 'accounts:dashboard'):
                target_url = reverse_safely(nm)
                if target_url:
                    break
        elif role in ('teacher', 'instructor'):
            for nm in ('instructor:dashboard', 'teachers:dashboard', 'accounts:instructor_dashboard', 'accounts:dashboard'):
                target_url = reverse_safely(nm)
                if target_url:
                    break
        elif role == 'parent':
            for nm in ('parents:dashboard', 'parent:dashboard', 'accounts:parent_dashboard', 'accounts:dashboard'):
                target_url = reverse_safely(nm)
                if target_url:
                    break
        else:
            target_url = reverse_safely('accounts:dashboard') or reverse_safely('home')

        # If user is hitting a generic page, route to their dashboard
        if target_url:
            generic_entry = (resolved_name in SAFE_PUBLIC) or (request.path in ('/', '/home/', '/dashboard/', '/accounts/'))
            on_profile_setup = (
                request.path.startswith('/accounts/profile-setup/') or request.path == '/accounts/profile-setup/' or
                request.path.startswith('/auth/profile-setup/') or request.path == '/auth/profile-setup/'
            )
            if generic_entry and not on_profile_setup and resolved_name not in SAFE_ALWAYS:
                if request.path != target_url:
                    return redirect(target_url)

        return None
