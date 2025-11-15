from rest_framework import serializers
from .models import Notification, Announcement, ScheduledReminder
from groups.serializers import KikobaSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class NotificationSerializer(serializers.ModelSerializer):
    group_name = serializers.SerializerMethodField() 
    
    class Meta:
        model = Notification
        fields = ('id', 'user', 'kikoba', 'group_name', 'type', 'title', 'message', 'created_at', 'is_read')
        read_only_fields = ('id', 'user', 'kikoba', 'type', 'title', 'message', 'created_at')
    
    def get_group_name(self, obj):
        if obj.kikoba:
            return obj.kikoba.name
        return None

class AnnouncementSerializer(serializers.ModelSerializer):
    group_name = serializers.SerializerMethodField()
    sender_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Announcement
        fields = ('id', 'kikoba', 'group_name', 'sender', 'sender_name', 'title', 'message', 'created_at')
        read_only_fields = ('id', 'sender', 'created_at')
    
    def get_group_name(self, obj):
        return obj.kikoba.name
    
    def get_sender_name(self, obj):
        return obj.sender.name
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['sender'] = user
        return super().create(validated_data)

class ScheduledReminderSerializer(serializers.ModelSerializer):
    group_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ScheduledReminder
        fields = ('id', 'kikoba', 'group_name', 'type', 'frequency', 'day_of_week', 'day_of_month', 'is_active')
    
    def get_group_name(self, obj):
        return obj.kikoba.name
