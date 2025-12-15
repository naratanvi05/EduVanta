from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.conf import settings

UserModel = get_user_model()

class EmailOrUsernameBackend(ModelBackend):
    """Authenticate with either username or email (case-insensitive for email)."""
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        if username is None or password is None:
            return None
        # Try username OR email
        try:
            user = UserModel.objects.get(Q(username__iexact=username) | Q(email__iexact=username))
        except UserModel.DoesNotExist:
            return None
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        return None


class AdminOnlyBackend(ModelBackend):
    """
    Authenticate only a single configured admin user (username or email must match, and password must match).
    Creates/updates the user with is_staff/is_superuser on successful auth.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        admin_username = getattr(settings, 'ADMIN_ONLY_USERNAME', '')
        admin_email = getattr(settings, 'ADMIN_ONLY_EMAIL', '')
        admin_password = getattr(settings, 'ADMIN_ONLY_PASSWORD', '')

        if not (admin_username and admin_email and admin_password):
            return None

        provided = username or kwargs.get('email') or kwargs.get('username')
        if not provided:
            return None

        # match username OR email
        if provided != admin_username and provided != admin_email:
            return None
        if password != admin_password:
            return None

        user, _ = UserModel.objects.get_or_create(
            username=admin_username,
            defaults={'email': admin_email, 'is_staff': True, 'is_superuser': True}
        )
        changed = False
        if user.email != admin_email:
            user.email = admin_email
            changed = True
        if not user.is_staff:
            user.is_staff = True
            changed = True
        if not user.is_superuser:
            user.is_superuser = True
            changed = True
        if not user.check_password(admin_password):
            user.set_password(admin_password)
            changed = True
        if changed:
            user.save()
        return user
