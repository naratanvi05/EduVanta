from django.urls import path
from . import views

app_name = 'announcements'

urlpatterns = [
    path('', views.announcement_list, name='announcement_list'),
    path('create/', views.create_announcement, name='create_announcement'),
    path('<int:pk>/edit/', views.edit_announcement, name='edit_announcement'),
    path('<int:pk>/delete/', views.delete_announcement, name='delete_announcement'),
    path('<int:pk>/', views.announcement_detail, name='announcement_detail'),
]
