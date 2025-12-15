from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from accounts.models import User, ParentChildLink, ParentInvite, InviteDelivery, Notification, ParentLinkRequest

class Command(BaseCommand):
    help = "Remove linked artifacts for given emails (parents/students). Optionally delete users as well."

    def add_arguments(self, parser):
        parser.add_argument('--emails', nargs='+', required=True, help='Email addresses to clean (space-separated)')
        parser.add_argument('--delete-users', action='store_true', help='Also delete the user accounts after cleanup')

    @transaction.atomic
    def handle(self, *args, **options):
        emails = [e.strip().lower() for e in options['emails'] if e.strip()]
        if not emails:
            raise CommandError('No emails provided')

        self.stdout.write(self.style.NOTICE(f"Cleaning artifacts for {len(emails)} email(s)..."))

        # Parent-child links
        pcl_parent = ParentChildLink.objects.filter(parent__email__in=emails)
        pcl_child = ParentChildLink.objects.filter(child__email__in=emails)
        pcl_count = pcl_parent.count() + pcl_child.count()
        pcl_parent.delete(); pcl_child.delete()

        # Parent link requests
        plr_parent = ParentLinkRequest.objects.filter(parent__email__in=emails)
        plr_student = ParentLinkRequest.objects.filter(student__email__in=emails)
        plr_count = plr_parent.count() + plr_student.count()
        plr_parent.delete(); plr_student.delete()

        # Parent invites and deliveries
        inv_qs = ParentInvite.objects.filter(parent__email__in=emails) | ParentInvite.objects.filter(child_email__in=emails)
        inv_ids = list(inv_qs.values_list('id', flat=True))
        del_count_deliveries = InviteDelivery.objects.filter(invite_id__in=inv_ids).count()
        InviteDelivery.objects.filter(invite_id__in=inv_ids).delete()
        inv_count = inv_qs.count()
        inv_qs.delete()

        # Notifications
        notif_count = Notification.objects.filter(user__email__in=emails).count()
        Notification.objects.filter(user__email__in=emails).delete()

        # Optionally delete users
        user_count = 0
        if options.get('delete_users'):
            user_count = User.objects.filter(email__in=emails).count()
            User.objects.filter(email__in=emails).delete()

        self.stdout.write(self.style.SUCCESS(
            f"Removed: Links={pcl_count}, LinkRequests={plr_count}, Invites={inv_count}, Deliveries={del_count_deliveries}, Notifications={notif_count}."
        ))
        if options.get('delete_users'):
            self.stdout.write(self.style.SUCCESS(f"Deleted Users: {user_count}"))
        else:
            self.stdout.write(self.style.WARNING("Users retained (use --delete-users to delete)."))
