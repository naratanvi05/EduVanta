from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):  # Auto-create/update configured admin on startup
        try:
            from django.conf import settings
            from django.contrib.auth import get_user_model
            User = get_user_model()

            username = getattr(settings, 'ADMIN_ONLY_USERNAME', None)
            email = getattr(settings, 'ADMIN_ONLY_EMAIL', None)
            password = getattr(settings, 'ADMIN_ONLY_PASSWORD', None)
            if username and email and password:
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={'email': email, 'is_staff': True, 'is_superuser': True}
                )
                changed = False
                if user.email != email:
                    user.email = email
                    changed = True
                # Ensure admin role and verification
                if getattr(user, 'role', None) != 'admin':
                    try:
                        user.role = 'admin'
                        changed = True
                    except Exception:
                        pass
                if not user.is_staff:
                    user.is_staff = True
                    changed = True
                if not user.is_superuser:
                    user.is_superuser = True
                    changed = True
                # Mark admin as verified to avoid any OTP prompts anywhere it might still appear
                if hasattr(user, 'is_verified') and not user.is_verified:
                    try:
                        user.is_verified = True
                        changed = True
                    except Exception:
                        pass
                if not user.check_password(password):
                    user.set_password(password)
                    changed = True
                if changed:
                    user.save()
        except Exception:
            # Avoid hard failures during migrations/collectstatic
            pass
