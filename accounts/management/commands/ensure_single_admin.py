from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Ensure only the configured admin is superuser; demote others to non-staff.'

    def handle(self, *args, **options):
        User = get_user_model()
        username = getattr(settings, 'ADMIN_ONLY_USERNAME', None)
        email = getattr(settings, 'ADMIN_ONLY_EMAIL', None)
        password = getattr(settings, 'ADMIN_ONLY_PASSWORD', None)
        if not (username and email and password):
            self.stderr.write('ADMIN_ONLY_* settings missing; nothing to do.')
            return

        admin, created = User.objects.get_or_create(
            username=username,
            defaults={'email': email}
        )
        admin.email = email
        admin.is_staff = True
        admin.is_superuser = True
        # Ensure correct role and verification for the configured admin
        try:
            if getattr(admin, 'role', None) != 'admin':
                admin.role = 'admin'
            if hasattr(admin, 'is_verified') and not admin.is_verified:
                admin.is_verified = True
        except Exception:
            pass
        if not admin.check_password(password):
            admin.set_password(password)
        admin.save()

        demoted = (
            User.objects.filter(is_superuser=True)
            .exclude(pk=admin.pk)
            .update(is_superuser=False, is_staff=False)
        )
        self.stdout.write(self.style.SUCCESS(
            f"Ensured single admin '{username}'. Demoted {demoted} other superusers."
        ))
