from django.contrib import admin
from django.conf import settings
from django.template.loader import render_to_string
from django.urls import reverse, path
from .models import User, ParentChildLink, SiteSetting, ParentInvite, InviteDelivery, Notification, ParentLinkRequest
from .views import _send_email_with_fallback
from django.db.models import Count, Q
from django.db.models.functions import TruncDate, TruncWeek
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render
from django.http import HttpResponse
import csv


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "role", "is_verified", "is_staff")
    list_filter = ("role", "is_verified", "is_staff")
    search_fields = ("username", "email", "first_name", "last_name")
    actions = ["cleanup_user_artifacts"]

    def cleanup_user_artifacts(self, request, queryset):
        """Remove linked artifacts for selected users (parents/students):
        - ParentChildLink (as parent and as child)
        - ParentLinkRequest (as parent and as student)
        - ParentInvite (and InviteDelivery)
        - Notifications addressed to these users
        Does NOT delete the users themselves.
        """
        emails = list(queryset.values_list('email', flat=True))
        # Parent-child links
        pcl_parent = ParentChildLink.objects.filter(parent__email__in=emails)
        pcl_child = ParentChildLink.objects.filter(child__email__in=emails)
        pcl_count = pcl_parent.count() + pcl_child.count()
        pcl_parent.delete()
        pcl_child.delete()

        # Parent link requests
        plr_parent = ParentLinkRequest.objects.filter(parent__email__in=emails)
        plr_student = ParentLinkRequest.objects.filter(student__email__in=emails)
        plr_count = plr_parent.count() + plr_student.count()
        plr_parent.delete()
        plr_student.delete()

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

        self.message_user(
            request,
            f"Artifacts removed: Links={pcl_count}, LinkRequests={plr_count}, Invites={inv_count}, Deliveries={del_count_deliveries}, Notifications={notif_count}. Users retained.")
    cleanup_user_artifacts.short_description = "Cleanup linked artifacts for selected users"


@admin.register(ParentChildLink)
class ParentChildLinkAdmin(admin.ModelAdmin):
    list_display = ("parent", "child", "created_at")
    search_fields = ("parent__username", "parent__email", "child__username", "child__email")


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ("brand_name", "brand_color", "email_subject_prefix")
    fieldsets = (
        ("Branding", {
            'fields': ("brand_name", "brand_color", "logo_url"),
        }),
        ("Email", {
            'fields': ("email_subject_prefix",),
        }),
    )


class InviteDeliveryInline(admin.TabularInline):
    model = InviteDelivery
    extra = 0
    can_delete = False
    readonly_fields = ("to_email", "subject", "sent_at", "success", "error_text")
    fields = ("to_email", "subject", "sent_at", "success", "error_text")


@admin.register(ParentInvite)
class ParentInviteAdmin(admin.ModelAdmin):
    list_display = ("child_email", "parent", "is_accepted", "created_at", "total_sent", "total_failed", "last_delivery_time", "last_delivery_success")
    list_filter = ("is_accepted", "created_at")
    search_fields = ("child_email", "child_name", "parent__username", "parent__email")
    readonly_fields = ("token", "created_at")
    inlines = [InviteDeliveryInline]
    actions = ["action_resend_invites", "action_resend_failed_only"]
    change_list_template = 'admin/accounts/parentinvite_change_list.html'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Annotate totals to avoid extra queries in list_display
        qs = qs.annotate(
            _total_sent=Count('deliveries', distinct=True),
            _total_failed=Count('deliveries', filter=Q(deliveries__success=False), distinct=True),
        )
        return qs

    def last_delivery_time(self, obj):
        last = obj.deliveries.all().first() if hasattr(obj, 'deliveries') else None
        return last.sent_at if last else None
    last_delivery_time.short_description = "Last emailed"

    def last_delivery_success(self, obj):
        last = obj.deliveries.all().first() if hasattr(obj, 'deliveries') else None
        return last.success if last else None
    last_delivery_success.boolean = True
    last_delivery_success.short_description = "Last success"

    def total_sent(self, obj):
        return getattr(obj, '_total_sent', None) if getattr(obj, '_total_sent', None) is not None else obj.deliveries.count()
    total_sent.short_description = "Total sent"

    def total_failed(self, obj):
        return getattr(obj, '_total_failed', None) if getattr(obj, '_total_failed', None) is not None else obj.deliveries.filter(success=False).count()
    total_failed.short_description = "Total failed"

    def action_resend_invites(self, request, queryset):
        sent = 0
        failed = 0
        for inv in queryset.select_related('parent').prefetch_related('deliveries'):
            if inv.is_accepted:
                continue
            try:
                brand_name = getattr(settings, 'SITE_BRAND_NAME', 'EduVanta')
                brand_color = getattr(settings, 'SITE_BRAND_COLOR', '#4f46e5')
                logo_url = getattr(settings, 'SITE_BRAND_LOGO_URL', '')
                # Build absolute URL using admin request
                accept_path = reverse('accounts:accept_invite', args=[inv.token])
                accept_url = request.build_absolute_uri(accept_path)
                subject = f"{brand_name} Parent Invite (Bulk Resend)"
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
                InviteDelivery.objects.create(invite=inv, to_email=inv.child_email, subject='[ADMIN] Resend Exception', success=False, error_text=str(e))
                failed += 1
        self.message_user(request, f"Resend complete: {sent} sent, {failed} failed.")
    action_resend_invites.short_description = "Resend selected invites"

    def action_resend_failed_only(self, request, queryset):
        # Filter to only those with at least one failed delivery and not accepted
        queryset = queryset.filter(is_accepted=False, deliveries__success=False).distinct()
        sent = 0
        failed = 0
        for inv in queryset.select_related('parent').prefetch_related('deliveries'):
            try:
                brand_name = getattr(settings, 'SITE_BRAND_NAME', 'EduVanta')
                brand_color = getattr(settings, 'SITE_BRAND_COLOR', '#4f46e5')
                logo_url = getattr(settings, 'SITE_BRAND_LOGO_URL', '')
                accept_path = reverse('accounts:accept_invite', args=[inv.token])
                accept_url = request.build_absolute_uri(accept_path)
                subject = f"{brand_name} Parent Invite (Bulk Resend: Failed Only)"
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
                InviteDelivery.objects.create(invite=inv, to_email=inv.child_email, subject='[ADMIN] Resend Failed-Only Exception', success=False, error_text=str(e))
                failed += 1
        self.message_user(request, f"Resend (failed only) complete: {sent} sent, {failed} failed.")
    action_resend_failed_only.short_description = "Resend failed only"

    # Custom admin analytics view
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path('analytics/', self.admin_site.admin_view(self.analytics_view), name='accounts_parentinvite_analytics'),
            path('analytics/export/', self.admin_site.admin_view(self.analytics_export), name='accounts_parentinvite_analytics_export'),
        ]
        return custom + urls

    def analytics_view(self, request):
        # Time window
        days = int(request.GET.get('days', '30'))
        since = timezone.now() - timedelta(days=days)
        qs = InviteDelivery.objects.all()
        if days > 0:
            qs = qs.filter(sent_at__gte=since)

        # By day
        by_day = (
            qs.annotate(day=TruncDate('sent_at'))
              .values('day')
              .annotate(total=Count('id'), ok=Count('id', filter=Q(success=True)))
              .order_by('day')
        )
        day_labels = [row['day'].strftime('%Y-%m-%d') for row in by_day]
        day_total = [int(row['total'] or 0) for row in by_day]
        day_ok = [int(row['ok'] or 0) for row in by_day]

        # By week
        by_week = (
            qs.annotate(week=TruncWeek('sent_at'))
              .values('week')
              .annotate(total=Count('id'), ok=Count('id', filter=Q(success=True)))
              .order_by('week')
        )
        week_labels = [row['week'].date().isoformat() for row in by_week]
        week_total = [int(row['total'] or 0) for row in by_week]
        week_ok = [int(row['ok'] or 0) for row in by_week]

        total = qs.count()
        ok_count = qs.filter(success=True).count()
        fail_count = total - ok_count
        success_rate = (ok_count / total * 100.0) if total else 0.0

        # Top domains by failure (Python aggregation for portability)
        domain_counts = {}
        for row in qs.values('to_email', 'success'):
            email = row['to_email'] or ''
            dom = email.split('@')[-1].lower() if '@' in email else ''
            if dom not in domain_counts:
                domain_counts[dom] = {'failed': 0, 'total': 0}
            domain_counts[dom]['total'] += 1
            if not row['success']:
                domain_counts[dom]['failed'] += 1
        top_domains = [
            {
                'domain': dom or '(unknown)',
                'failed': vals['failed'],
                'total': vals['total'],
                'fail_rate': (vals['failed'] / vals['total'] * 100.0) if vals['total'] else 0.0,
            }
            for dom, vals in domain_counts.items()
            if vals['failed'] > 0
        ]
        top_domains.sort(key=lambda x: (x['failed'], x['total']), reverse=True)
        top_domains = top_domains[:10]

        # Domain diagnostics: flag domains with persistent high failure rate
        bad_domains = []
        for dom, vals in domain_counts.items():
            total_d = vals['total']
            failed_d = vals['failed']
            if total_d >= 5 and failed_d / total_d >= 0.5:  # 50%+ failures with at least 5 attempts
                bad_domains.append({
                    'domain': dom or '(unknown)',
                    'failed': failed_d,
                    'total': total_d,
                    'fail_rate': (failed_d / total_d * 100.0),
                })
        bad_domains.sort(key=lambda x: (x['fail_rate'], x['total']), reverse=True)

        # Per-parent outcomes
        per_parent_qs = (
            qs.values('invite__parent_id', 'invite__parent__email')
              .annotate(total=Count('id'), ok=Count('id', filter=Q(success=True)))
              .order_by('-total')
        )
        per_parent = []
        for row in per_parent_qs:
            total_p = int(row.get('total') or 0)
            ok_p = int(row.get('ok') or 0)
            rate_p = (ok_p / total_p * 100.0) if total_p else 0.0
            per_parent.append({
                'parent_email': row.get('invite__parent__email') or '(unknown)',
                'total': total_p,
                'ok': ok_p,
                'success_rate': rate_p,
            })

        context = dict(
            self.admin_site.each_context(request),
            title='Parent Invite Analytics',
            days=days,
            total=total,
            ok_count=ok_count,
            fail_count=fail_count,
            success_rate=success_rate,
            day_labels=day_labels,
            day_total=day_total,
            day_ok=day_ok,
            week_labels=week_labels,
            week_total=week_total,
            week_ok=week_ok,
            top_domains=top_domains,
            bad_domains=bad_domains,
            per_parent=per_parent,
        )
        return render(request, 'admin/accounts/parentinvite_analytics.html', context)

    def analytics_export(self, request):
        days = int(request.GET.get('days', '30'))
        since = timezone.now() - timedelta(days=days)
        qs = InviteDelivery.objects.select_related('invite__parent').all()
        if days > 0:
            qs = qs.filter(sent_at__gte=since)
        # Stream CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="invite_deliveries.csv"'
        writer = csv.writer(response)
        writer.writerow(['sent_at', 'to_email', 'subject', 'success', 'error_text', 'invite_id', 'parent_id', 'parent_email'])
        for d in qs.order_by('-sent_at'):
            parent = getattr(d.invite, 'parent', None)
            writer.writerow([
                d.sent_at.isoformat() if d.sent_at else '',
                d.to_email,
                d.subject,
                '1' if d.success else '0',
                (d.error_text or '').replace('\n', ' ').replace('\r', ' '),
                d.invite_id,
                getattr(parent, 'id', ''),
                getattr(parent, 'email', ''),
            ])
        return response

class HasSuccessfulDeliveryFilter(admin.SimpleListFilter):
    title = 'has successful delivery'
    parameter_name = 'has_success'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Yes'),
            ('no', 'No'),
        )

    def queryset(self, request, queryset):
        val = self.value()
        if val == 'yes':
            return queryset.filter(deliveries__success=True).distinct()
        if val == 'no':
            return queryset.exclude(deliveries__success=True).distinct()
        return queryset

# Attach custom filter
ParentInviteAdmin.list_filter = ParentInviteAdmin.list_filter + (HasSuccessfulDeliveryFilter,)

class TopParentFailuresFilter(admin.SimpleListFilter):
    title = 'top parent failures'
    parameter_name = 'parent_fail'

    def lookups(self, request, model_admin):
        # Compute top 10 parents by failed deliveries
        agg = (
            InviteDelivery.objects.values('invite__parent_id', 'invite__parent__email')
            .annotate(failed=Count('id', filter=Q(success=False)), total=Count('id'))
            .filter(failed__gt=0)
            .order_by('-failed', '-total')[:10]
        )
        return [
            (str(row['invite__parent_id'] or ''), f"{row['invite__parent__email'] or '(unknown)'} ({row['failed']}/{row['total']})")
            for row in agg
        ]

    def queryset(self, request, queryset):
        val = self.value()
        if val:
            try:
                pid = int(val)
                return queryset.filter(parent_id=pid)
            except Exception:
                return queryset
        return queryset

# Attach custom top failures filter
ParentInviteAdmin.list_filter = ParentInviteAdmin.list_filter + (TopParentFailuresFilter,)


@admin.register(InviteDelivery)
class InviteDeliveryAdmin(admin.ModelAdmin):
    list_display = ("to_email", "subject", "success", "sent_at", "invite",)
    list_filter = ("success", "sent_at")
    search_fields = ("to_email", "subject", "invite__child_email", "invite__parent__username", "invite__parent__email")
    readonly_fields = ("invite", "to_email", "subject", "sent_at", "success", "error_text")


# ---- Notifications Admin ----
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "category", "severity", "title", "is_read", "read_at", "created_at")
    list_filter = ("category", "severity", "is_read")
    search_fields = ("title", "user__username", "user__email")
