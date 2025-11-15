from django.shortcuts import render
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Notification, Announcement, ScheduledReminder
from .serializers import NotificationSerializer, AnnouncementSerializer, ScheduledReminderSerializer
from groups.models import KikobaMembership, Kikoba
from django.db.models import Q
from django.utils import timezone

class IsKikobaAdmin(permissions.BasePermission):
    """
    Custom permission to only allow kikoba admins to perform certain actions.
    """
    def has_object_permission(self, request, view, obj):
        # For announcements and reminders, check if user is an admin in the kikoba
        if hasattr(obj, 'kikoba'):
            return KikobaMembership.objects.filter(
                kikoba=obj.kikoba,
                user=request.user,
                role__in=['chairperson', 'treasurer', 'secretary', 'kikoba_admin'],
                is_active=True
            ).exists()
        return False

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'is_read']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        
        serializer = self.get_serializer(notification)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        notifications = self.get_queryset().filter(is_read=False)
        notifications.update(is_read=True)
        
        return Response({'status': 'success', 'message': f'{notifications.count()} notifications marked as read'})

class AnnouncementViewSet(viewsets.ModelViewSet):
    serializer_class = AnnouncementSerializer
    permission_classes = [permissions.IsAuthenticated, IsKikobaAdmin]
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    search_fields = ['title', 'message']
    
    def get_queryset(self):
        user = self.request.user
        
        # Get vikoba where user is a member
        user_vikoba = KikobaMembership.objects.filter(
            user=user,
            is_active=True
        ).values_list('kikoba', flat=True)
        
        return Announcement.objects.filter(kikoba__in=user_vikoba)
    
    def perform_create(self, serializer):
        kikoba = serializer.validated_data.get('kikoba')
        
        # Check if user is an admin in this kikoba
        is_admin = KikobaMembership.objects.filter(
            user=self.request.user,
            kikoba=kikoba,
            role__in=['chairperson', 'treasurer', 'secretary', 'kikoba_admin'],
            is_active=True
        ).exists()
        
        if not is_admin:
            raise permissions.PermissionDenied("You must be a kikoba admin to create announcements")
        
        serializer.save(sender=self.request.user)

class ScheduledReminderViewSet(viewsets.ModelViewSet):
    serializer_class = ScheduledReminderSerializer
    permission_classes = [permissions.IsAuthenticated, IsKikobaAdmin]
    
    def get_queryset(self):
        user = self.request.user
        
        # Get vikoba where user is an admin
        admin_vikoba = KikobaMembership.objects.filter(
            user=user,
            role__in=['chairperson', 'treasurer', 'kikoba_admin'],
            is_active=True
        ).values_list('kikoba', flat=True)
        
        return ScheduledReminder.objects.filter(kikoba__in=admin_vikoba)
