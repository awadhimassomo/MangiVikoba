"""
URL configuration for mangikikoba project.

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
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from registration.views import (
    custom_logout, 
    PasswordResetRequestOTPView,
    PasswordResetVerifyOTPView,
    PasswordResetChangePINView
)
from registration.auth_views import CustomLoginView
from registration.forms import PINSetPasswordForm

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/logout/', custom_logout, name='logout'),
    path('accounts/login/', CustomLoginView.as_view(template_name='registration/login.html'), name='login'),
    
    # OTP-based PIN reset flow (3 steps)
    path('accounts/password_reset/', 
         PasswordResetRequestOTPView.as_view(), 
         name='password_reset_request'),
    path('accounts/password_reset/verify-otp/', 
         PasswordResetVerifyOTPView.as_view(), 
         name='password_reset_verify_otp'),
    path('accounts/password_reset/change-pin/', 
         PasswordResetChangePINView.as_view(), 
         name='password_reset_change_pin'),
    
    # Note: We don't include django.contrib.auth.urls because we've defined custom views above
    path('dashboard/', include('dashboard.urls')), # Added dashboard urls
    
    # REST API v1 - Main API for mobile app
    path('api/', include('dashboard.api_urls')),  # Include dashboard API endpoints
    path('api/v1/', include('api.urls')),
    
    # Legacy API endpoints (if still in use)
    path('api/auth/', include('registration.urls')),
    path('api/groups/', include('groups.urls')),
    path('api/savings/', include('savings.urls')),
    path('api/loans/', include('loans.urls')),
    path('api/learning/', include('learning.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/reports/', include('reports.urls')),
    
    # Frontend pages
    path('', include('landing.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
