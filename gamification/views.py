from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.conf import settings
from django.core.mail import EmailMessage
from django.core.paginator import Paginator
from django.db.models import Count, Q

from .models import Challenge, ChallengeParticipation


@login_required
def challenges_list(request):
    # Student-only
    if getattr(request.user, 'role', None) != 'student':
        return render(request, 'gamification/challenges_list.html', {
            'challenges': [],
            'now': timezone.now(),
            'not_student': True,
        })
    now = timezone.now()
    qs = (Challenge.objects
          .filter(is_active=True, is_deleted=False, is_approved=True)
          .order_by('-start_at'))
    # Optionally filter to date window if provided
    active = []
    for c in qs:
        if c.start_at and c.start_at > now:
            continue
        if c.end_at and c.end_at < now:
            continue
        active.append(c)
    return render(request, 'gamification/challenges_list.html', {
        'challenges': active,
        'now': now,
        'not_student': False,
    })


# -------------------- Teacher challenge management --------------------

def _require_teacher(user):
    return bool(getattr(user, 'is_authenticated', False) and (getattr(user, 'role', None) == 'teacher' or getattr(user, 'is_staff', False)))


@login_required
def teacher_my_challenges(request):
    if not _require_teacher(request.user):
        return redirect('accounts:dashboard')
    qs = (Challenge.objects
          .filter(created_by=request.user)
          .annotate(
              participation_count=Count('participations', distinct=True),
              completed_count=Count('participations', filter=Q(participations__status='completed'), distinct=True),
          ))
    # Filters: q (title search), status (pending|approved|deleted|active|inactive)
    q = (request.GET.get('q') or '').strip()
    status = (request.GET.get('status') or '').strip()
    if q:
        qs = qs.filter(title__icontains=q)
    if status == 'pending':
        qs = qs.filter(is_approved=False, is_deleted=False)
    elif status == 'approved':
        qs = qs.filter(is_approved=True, is_deleted=False)
    elif status == 'deleted':
        qs = qs.filter(is_deleted=True)
    elif status == 'active':
        qs = qs.filter(is_active=True, is_deleted=False)
    elif status == 'inactive':
        qs = qs.filter(is_active=False, is_deleted=False)
    qs = qs.order_by('-created_at')
    paginator = Paginator(qs, 10)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)
    return render(request, 'gamification/teacher_my_challenges.html', {
        'items': page_obj.object_list,
        'page_obj': page_obj,
        'q': q,
        'status': status,
    })


@login_required
def teacher_create_challenge(request):
    if not _require_teacher(request.user):
        return redirect('accounts:dashboard')
    ctx = {}
    if request.method == 'POST':
        title = (request.POST.get('title') or '').strip()
        description = (request.POST.get('description') or '').strip()
        xp_reward = int(request.POST.get('xp_reward') or 0)
        start_at = request.POST.get('start_at') or None
        end_at = request.POST.get('end_at') or None
        import datetime
        # Basic validation
        errors = []
        if not title:
            errors.append('Title is required.')
        if xp_reward <= 0:
            errors.append('XP reward must be greater than 0.')
        # Parse datetimes if given
        def parse_dt(s):
            if not s:
                return None
            try:
                # Expecting HTML datetime-local input: YYYY-MM-DDTHH:MM
                return datetime.datetime.fromisoformat(s)
            except Exception:
                return None
        start_dt = parse_dt(start_at)
        end_dt = parse_dt(end_at)
        if errors:
            ctx['errors'] = errors
        else:
            # Slug: derive from title; ensure uniqueness
            from django.utils.text import slugify
            base = slugify(title)[:200]
            slug = base
            i = 1
            while Challenge.objects.filter(slug=slug).exists():
                i += 1
                slug = f"{base}-{i}"
            Challenge.objects.create(
                title=title,
                description=description,
                xp_reward=xp_reward,
                start_at=start_dt,
                end_at=end_dt,
                slug=slug,
                is_active=True,
                is_deleted=False,
                is_approved=False,  # Requires approval to be visible to students
                created_by=request.user,
            )
            messages.success(request, 'Challenge created. Awaiting admin approval.')
            return redirect('gamification:teacher_my_challenges')
    # GET or validation errors fall-through
    return render(request, 'gamification/teacher_challenge_form.html', ctx)


# -------------------- Student: My challenge progress --------------------

@login_required
def student_my_challenges_progress(request):
    if getattr(request.user, 'role', None) != 'student':
        return redirect('accounts:dashboard')
    parts = (ChallengeParticipation.objects
             .select_related('challenge')
             .filter(student=request.user)
             .order_by('-created_at'))
    return render(request, 'gamification/student_my_challenges.html', {'parts': parts})


# -------------------- Teacher: Participations list --------------------

@login_required
def teacher_challenge_participations(request, pk: int):
    if not _require_teacher(request.user):
        return redirect('accounts:dashboard')
    ch = get_object_or_404(Challenge, pk=pk, created_by=request.user)
    parts = (ChallengeParticipation.objects
             .select_related('student')
             .filter(challenge=ch)
             .order_by('-created_at'))
    return render(request, 'gamification/teacher_challenge_participations.html', {'challenge': ch, 'parts': parts})


# -------------------- Teacher: Edit challenge --------------------

@login_required
def teacher_edit_challenge(request, pk: int):
    if not _require_teacher(request.user):
        return redirect('accounts:dashboard')
    ch = get_object_or_404(Challenge, pk=pk, created_by=request.user)
    ctx = {'item': ch}
    if request.method == 'POST':
        title = (request.POST.get('title') or '').strip()
        description = (request.POST.get('description') or '').strip()
        xp_reward = int(request.POST.get('xp_reward') or 0)
        start_at = request.POST.get('start_at') or None
        end_at = request.POST.get('end_at') or None
        import datetime
        errors = []
        if not title:
            errors.append('Title is required.')
        if xp_reward <= 0:
            errors.append('XP reward must be greater than 0.')
        def parse_dt(s):
            if not s:
                return None
            try:
                return datetime.datetime.fromisoformat(s)
            except Exception:
                return None
        start_dt = parse_dt(start_at)
        end_dt = parse_dt(end_at)
        if errors:
            ctx['errors'] = errors
        else:
            ch.title = title
            ch.description = description
            ch.xp_reward = xp_reward
            ch.start_at = start_dt
            ch.end_at = end_dt
            ch.save()
            messages.success(request, 'Challenge updated (subject to approval visibility).')
            return redirect('gamification:teacher_my_challenges')
    return render(request, 'gamification/teacher_challenge_form.html', ctx)


# -------------------- Admin review --------------------

def _require_staff(user):
    return bool(getattr(user, 'is_authenticated', False) and getattr(user, 'is_staff', False))


@login_required
def admin_challenges(request):
    if not _require_staff(request.user):
        return redirect('accounts:dashboard')
    qs = Challenge.objects.all()
    q = (request.GET.get('q') or '').strip()
    status = (request.GET.get('status') or '').strip()
    if q:
        qs = qs.filter(title__icontains=q)
    if status == 'pending':
        qs = qs.filter(is_approved=False, is_deleted=False)
    elif status == 'approved':
        qs = qs.filter(is_approved=True, is_deleted=False)
    elif status == 'deleted':
        qs = qs.filter(is_deleted=True)
    elif status == 'active':
        qs = qs.filter(is_active=True, is_deleted=False)
    elif status == 'inactive':
        qs = qs.filter(is_active=False, is_deleted=False)
    qs = qs.order_by('-created_at')
    paginator = Paginator(qs, 15)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)
    return render(request, 'gamification/admin_challenges.html', {
        'items': page_obj.object_list,
        'page_obj': page_obj,
        'q': q,
        'status': status,
    })


@login_required
def admin_approve_challenge(request, pk: int):
    if not _require_staff(request.user):
        return redirect('accounts:dashboard')
    ch = get_object_or_404(Challenge, pk=pk)
    if request.method == 'POST':
        ch.is_approved = True
        ch.is_active = True
        ch.is_deleted = False
        ch.save(update_fields=['is_approved', 'is_active', 'is_deleted'])
        # Notify creator via Notification and Email
        try:
            from accounts.models import Notification
            if ch.created_by:
                Notification.objects.create(
                    user=ch.created_by,
                    category='gamification',
                    severity='success',
                    title='Challenge Approved',
                    body=f'Your challenge "{ch.title}" has been approved and published.'
                )
                if ch.created_by.email:
                    subject = f"{getattr(settings, 'SITE_EMAIL_SUBJECT_PREFIX', '[EduVanta]')} Challenge Approved".strip()
                    html = f"<p>Hi {ch.created_by.username},</p><p>Your challenge <strong>{ch.title}</strong> has been approved and is now visible to students.</p>"
                    email = EmailMessage(subject, html, settings.DEFAULT_FROM_EMAIL, [ch.created_by.email])
                    email.content_subtype = 'html'
                    email.send(fail_silently=True)
        except Exception:
            pass
        messages.success(request, 'Challenge approved and published to students.')
    return redirect('gamification:admin_challenges')


@login_required
def admin_unapprove_challenge(request, pk: int):
    if not _require_staff(request.user):
        return redirect('accounts:dashboard')
    ch = get_object_or_404(Challenge, pk=pk)
    if request.method == 'POST':
        ch.is_approved = False
        ch.save(update_fields=['is_approved'])
        messages.info(request, 'Challenge unapproved (hidden from students).')
    return redirect('gamification:admin_challenges')


@login_required
def admin_delete_challenge(request, pk: int):
    if not _require_staff(request.user):
        return redirect('accounts:dashboard')
    ch = get_object_or_404(Challenge, pk=pk)
    if request.method == 'POST':
        ch.is_deleted = True
        ch.is_active = False
        ch.save(update_fields=['is_deleted', 'is_active'])
        messages.success(request, 'Challenge deleted.')
    return redirect('gamification:admin_challenges')


@login_required
def admin_restore_challenge(request, pk: int):
    if not _require_staff(request.user):
        return redirect('accounts:dashboard')
    ch = get_object_or_404(Challenge, pk=pk)
    if request.method == 'POST':
        ch.is_deleted = False
        ch.save(update_fields=['is_deleted'])
        messages.success(request, 'Challenge restored (still requires approval to be visible).')
    return redirect('gamification:admin_challenges')


@login_required
def teacher_delete_challenge(request, pk: int):
    if not _require_teacher(request.user):
        return redirect('accounts:dashboard')
    ch = get_object_or_404(Challenge, pk=pk, created_by=request.user)
    if request.method == 'POST':
        ch.is_deleted = True
        ch.is_active = False
        ch.save(update_fields=['is_deleted', 'is_active'])
        messages.success(request, 'Challenge deleted. You can restore it anytime.')
    return redirect('gamification:teacher_my_challenges')


@login_required
def teacher_restore_challenge(request, pk: int):
    if not _require_teacher(request.user):
        return redirect('accounts:dashboard')
    ch = get_object_or_404(Challenge, pk=pk, created_by=request.user)
    if request.method == 'POST':
        ch.is_deleted = False
        # Do not auto-approve or auto-activate
        ch.save(update_fields=['is_deleted'])
        messages.success(request, 'Challenge restored. Submit for approval if needed.')
    return redirect('gamification:teacher_my_challenges')
