from django.shortcuts import render, get_object_or_404, redirect
from rest_framework import viewsets
from .models import Announcement
from .serializers import AnnouncementSerializer
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib import messages
from django.db.models import Q
from .models import Category

# Create your views here.

def announcement_list(request):
    qs = Announcement.objects.select_related('category', 'posted_by').order_by('-created_at')
    # Filtering by category id or slug
    cat = request.GET.get('category')
    if cat:
        if cat.isdigit():
            qs = qs.filter(category_id=int(cat))
        else:
            qs = qs.filter(category__slug=cat)
    # Search on title or content
    term = (request.GET.get('search') or '').strip()
    if term:
        qs = qs.filter(Q(title__icontains=term) | Q(content__icontains=term))

    categories = list(Category.objects.all())
    show_ai = bool((getattr(request.user, 'role', '') or '').lower() in ('admin', 'teacher', 'instructor') or getattr(request.user, 'is_staff', False))
    can_manage = show_ai
    context = {
        'announcements': qs,
        'categories': categories,
        'active_category': cat or '',
        'search_term': term,
        'show_ai': show_ai,
        'can_manage': can_manage,
    }
    return render(request, 'announcements/announcement_list.html', context)

def announcement_detail(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    can_manage = (getattr(request.user, 'is_staff', False) or (getattr(request.user, 'role', '') or '').lower() in ('admin', 'teacher', 'instructor'))
    return render(request, 'announcements/announcement_detail.html', {
        'announcement': announcement,
        'can_manage': can_manage,
    })


def _is_allowed_poster(user):
    """Allow Admin or Instructor/Teacher to manage announcements. Staff is always allowed.
    Be tolerant to role casing and synonyms (instructor/teacher).
    """
    if not user.is_authenticated:
        return False
    role = (getattr(user, 'role', '') or '').lower()
    return role in ('admin', 'teacher', 'instructor') or getattr(user, 'is_staff', False)


@login_required
@user_passes_test(_is_allowed_poster)
def create_announcement(request):
    """Create announcement (Admin/Instructor)."""
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        category_id = request.POST.get('category')
        if not title or not content:
            messages.error(request, 'Title and content are required.')
            return render(request, 'announcements/create_announcement.html', {
                'categories': Category.objects.all(),
                'form': {'title': title, 'content': content, 'category': category_id}
            })
        cat = None
        if category_id:
            try:
                cat = Category.objects.get(id=category_id)
            except Category.DoesNotExist:
                cat = None
        a = Announcement.objects.create(title=title, content=content, posted_by=request.user, category=cat)
        messages.success(request, 'Announcement created.')
        return redirect('announcements:announcement_detail', pk=a.pk)
    return render(request, 'announcements/create_announcement.html', {
        'categories': Category.objects.all()
    })


@login_required
@user_passes_test(_is_allowed_poster)
def edit_announcement(request, pk):
    ann = get_object_or_404(Announcement, pk=pk)
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        category_id = request.POST.get('category')
        if not title or not content:
            messages.error(request, 'Title and content are required.')
            return render(request, 'announcements/edit_announcement.html', {
                'categories': Category.objects.all(),
                'announcement': ann,
                'form': {'title': title, 'content': content, 'category': category_id}
            })
        cat = None
        if category_id:
            cat = Category.objects.filter(id=category_id).first()
        ann.title = title
        ann.content = content
        ann.category = cat
        ann.save()
        messages.success(request, 'Announcement updated.')
        return redirect('announcements:announcement_detail', pk=ann.pk)
    return render(request, 'announcements/edit_announcement.html', {
        'categories': Category.objects.all(),
        'announcement': ann,
        'form': {'title': ann.title, 'content': ann.content, 'category': getattr(ann.category, 'id', '')}
    })


@login_required
@user_passes_test(_is_allowed_poster)
def delete_announcement(request, pk):
    ann = get_object_or_404(Announcement, pk=pk)
    if request.method == 'POST':
        ann.delete()
        messages.success(request, 'Announcement deleted.')
        return redirect('announcements:announcement_list')
    # Safety: GET will just redirect to detail
    return redirect('announcements:announcement_detail', pk=pk)

class AnnouncementViewSet(viewsets.ModelViewSet):
    queryset = Announcement.objects.all()
    serializer_class = AnnouncementSerializer
    permission_classes = [IsAuthenticated]  # Restrict to authenticated users; refine permissions later
