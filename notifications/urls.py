from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet, AnnouncementViewSet, ScheduledReminderViewSet

router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'announcements', AnnouncementViewSet, basename='announcement')
router.register(r'reminders', ScheduledReminderViewSet, basename='reminder')

urlpatterns = [
    path('', include(router.urls)),
]
