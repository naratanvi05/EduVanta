from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from django.db.models.functions import TruncDate, TruncWeek
from accounts.models import InviteDelivery
from datetime import timedelta
from django.utils import timezone


class Command(BaseCommand):
    help = "Print analytics for parent invite deliveries: totals, success rate, breakdown by day and week, and top-N failure recipients."

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=30, help='Analyze only the last N days (default: 30). Use 0 for all time.')
        parser.add_argument('--top', type=int, default=10, help='Top N emails with most failures (default: 10)')

    def handle(self, *args, **options):
        days = options['days']
        top_n = options['top']

        qs = InviteDelivery.objects.all()
        if days and days > 0:
            since = timezone.now() - timedelta(days=days)
            qs = qs.filter(sent_at__gte=since)

        total = qs.count()
        successes = qs.filter(success=True).count()
        failures = total - successes
        success_rate = (successes / total * 100.0) if total else 0.0

        self.stdout.write(self.style.MIGRATE_HEADING('Invite Delivery Analytics'))
        window = f"last {days} days" if days and days > 0 else "all time"
        self.stdout.write(f"Window: {window}")
        self.stdout.write("")

        # Totals
        self.stdout.write(self.style.HTTP_INFO('Totals'))
        self.stdout.write(f"Total deliveries: {total}")
        self.stdout.write(f"Successful: {successes}")
        self.stdout.write(f"Failed: {failures}")
        self.stdout.write(f"Success rate: {success_rate:.2f}%")
        self.stdout.write("")

        # Breakdown by day
        self.stdout.write(self.style.HTTP_INFO('By Day'))
        by_day = (
            qs.annotate(day=TruncDate('sent_at'))
              .values('day')
              .annotate(total=Count('id'), ok=Count('id', filter=Q(success=True)))
              .order_by('day')
        )
        if not by_day:
            self.stdout.write("(no data)")
        else:
            for row in by_day:
                day_total = row['total'] or 0
                day_ok = row['ok'] or 0
                rate = (day_ok / day_total * 100.0) if day_total else 0.0
                self.stdout.write(f"{row['day']}: total={day_total} ok={day_ok} rate={rate:.1f}%")
        self.stdout.write("")

        # Breakdown by week
        self.stdout.write(self.style.HTTP_INFO('By Week'))
        by_week = (
            qs.annotate(week=TruncWeek('sent_at'))
              .values('week')
              .annotate(total=Count('id'), ok=Count('id', filter=Q(success=True)))
              .order_by('week')
        )
        if not by_week:
            self.stdout.write("(no data)")
        else:
            for row in by_week:
                w_total = row['total'] or 0
                w_ok = row['ok'] or 0
                rate = (w_ok / w_total * 100.0) if w_total else 0.0
                self.stdout.write(f"{row['week'].date()}: total={w_total} ok={w_ok} rate={rate:.1f}%")
        self.stdout.write("")

        # Top failure recipients
        self.stdout.write(self.style.HTTP_INFO(f'Top {top_n} emails with most failures'))
        top_fail = (
            qs.values('to_email')
              .annotate(failed=Count('id', filter=Q(success=False)), total=Count('id'))
              .filter(failed__gt=0)
              .order_by('-failed', '-total')[:top_n]
        )
        if not top_fail:
            self.stdout.write("(no failures)")
        else:
            for row in top_fail:
                email = row['to_email']
                failed = row['failed'] or 0
                t = row['total'] or 0
                rate_fail = (failed / t * 100.0) if t else 0.0
                self.stdout.write(f"{email}: failed={failed} / total={t} ({rate_fail:.1f}% failure)")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS('Analytics complete.'))
