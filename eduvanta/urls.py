"""
URL configuration for eduvanta project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.contrib.auth import views as auth_views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from accounts.views import send_otp, verify_otp, register_user, profile_setup
from announcements.views import AnnouncementViewSet
from courses.views import CourseViewSet
from . import views
from django.views.generic import TemplateView, RedirectView

router = DefaultRouter()
router.register(r'announcements', AnnouncementViewSet, basename='announcement')
router.register(r'courses', CourseViewSet, basename='course')

urlpatterns = [
    path('', views.home, name='home'),
    path('admin/', admin.site.urls),
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),
    path('courses/', include(('courses.urls', 'courses'), namespace='courses')),
    path('announcements/', include(('announcements.urls', 'announcements'), namespace='announcements')),
    path('gamification/', include(('gamification.urls', 'gamification'), namespace='gamification')),
    path('social-auth/', include('social_django.urls', namespace='social')),
    # Root-level password reset routes (un-namespaced) used by Django auth views/email templates
    path('accounts/password_reset/', auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset.html'
    ), name='password_reset'),
    path('accounts/password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html'
    ), name='password_reset_done'),
    # Root-level alias so the default email template can reverse 'password_reset_confirm'
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html'
    ), name='password_reset_complete'),
    # Alias route for profile setup wizard
    path('auth/profile-setup/', RedirectView.as_view(url='/accounts/profile-setup/', permanent=False), name='auth_profile_setup'),
    # Legal pages
    path('legal/privacy/', TemplateView.as_view(template_name='legal/privacy.html'), name='privacy'),
    path('legal/terms/', TemplateView.as_view(template_name='legal/terms.html'), name='terms'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/send-otp/', send_otp, name='send_otp'),
    path('api/verify-otp/', verify_otp, name='verify_otp'),
    path('api/register/', register_user, name='register_user'),
    path('api/profile-setup/', profile_setup, name='profile_setup'),
    path('api/', include(router.urls)),  # Include the router for announcements API
]
