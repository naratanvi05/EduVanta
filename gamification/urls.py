from django.urls import path
from . import views

app_name = 'gamification'

urlpatterns = [
    path('challenges/', views.challenges_list, name='challenges_list'),
    path('my/challenges/', views.student_my_challenges_progress, name='student_my_challenges'),
    # Teacher
    path('teacher/challenges/', views.teacher_my_challenges, name='teacher_my_challenges'),
    path('teacher/challenges/new/', views.teacher_create_challenge, name='teacher_create_challenge'),
    path('teacher/challenges/<int:pk>/edit/', views.teacher_edit_challenge, name='teacher_edit_challenge'),
    path('teacher/challenges/<int:pk>/participations/', views.teacher_challenge_participations, name='teacher_challenge_participations'),
    path('teacher/challenges/<int:pk>/delete/', views.teacher_delete_challenge, name='teacher_delete_challenge'),
    path('teacher/challenges/<int:pk>/restore/', views.teacher_restore_challenge, name='teacher_restore_challenge'),
    # Admin/staff review
    path('admin/challenges/', views.admin_challenges, name='admin_challenges'),
    path('admin/challenges/<int:pk>/approve/', views.admin_approve_challenge, name='admin_approve_challenge'),
    path('admin/challenges/<int:pk>/unapprove/', views.admin_unapprove_challenge, name='admin_unapprove_challenge'),
    path('admin/challenges/<int:pk>/delete/', views.admin_delete_challenge, name='admin_delete_challenge'),
    path('admin/challenges/<int:pk>/restore/', views.admin_restore_challenge, name='admin_restore_challenge'),
]
