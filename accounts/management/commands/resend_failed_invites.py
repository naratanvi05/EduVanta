from django.core.management.base import BaseCommand
from django.conf import settings
from django.template.loader import render_to_string
from django.urls import reverse
from accounts.models import ParentInvite, InviteDelivery
from accounts.views import _send_email_with_fallback


class Command(BaseCommand):
    help = "Resend invite emails for ParentInvites that have at least one failed delivery and are not yet accepted."

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=100, help='Max invites to process (default: 100)')
        parser.add_argument('--only-never-success', action='store_true', help='Only resend for invites that have no successful deliveries yet')

    def handle(self, *args, **options):
        limit = options['limit']
        only_never_success = options['only_never_success']

        qs = ParentInvite.objects.filter(is_accepted=False)
        if only_never_success:
            qs = qs.exclude(deliveries__success=True)
        else:
            qs = qs.filter(deliveries__success=False)
        qs = qs.distinct().select_related('parent')[:limit]

        sent = 0
        failed = 0
        for inv in qs:
            try:
                brand_name = getattr(settings, 'SITE_BRAND_NAME', 'EduVanta')
                brand_color = getattr(settings, 'SITE_BRAND_COLOR', '#4f46e5')
                logo_url = getattr(settings, 'SITE_BRAND_LOGO_URL', '')
                # Build absolute URL path only; in management commands we may not have a request, so join with SITE_URL if available
                accept_path = reverse('accounts:accept_invite', args=[inv.token])
                site_url = getattr(settings, 'SITE_URL', '').rstrip('/')
                accept_url = f"{site_url}{accept_path}" if site_url else accept_path
                subject = f"{brand_name} Parent Invite (Automated Resend)"
                html = render_to_string('email/parent_invite.html', {
                    'brand_name': brand_name,
                    'brand_color': brand_color,
                    'logo_url': logo_url,
                    'accept_url': accept_url,
                    'parent': inv.parent,
                    'child_name': inv.child_name,
                    'child_email': inv.child_email,
                })
                ok, err = _send_email_with_fallback(subject, html, [inv.child_email])
                InviteDelivery.objects.create(invite=inv, to_email=inv.child_email, subject=subject, success=bool(ok), error_text=(err or ''))
                if ok:
                    sent += 1
                else:
                    failed += 1
            except Exception as e:
                InviteDelivery.objects.create(invite=inv, to_email=inv.child_email, subject='[MGMT] Resend Exception', success=False, error_text=str(e))
                failed += 1
        self.stdout.write(self.style.SUCCESS(f"Resend complete: {sent} sent, {failed} failed (processed {qs.count()} invites)."))
