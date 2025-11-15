from django.contrib import admin
from .models import Notification, Announcement, ScheduledReminder

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'type', 'get_kikoba_name', 'created_at', 'is_read')
    list_filter = ('type', 'is_read', 'created_at', 'kikoba')
    search_fields = ('user__username', 'title', 'message', 'kikoba__name') # Assuming user has a username field

    def get_kikoba_name(self, obj):
        if obj.kikoba:
            return obj.kikoba.name
        return None
    get_kikoba_name.short_description = 'Kikoba'

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'get_kikoba_name', 'sender', 'created_at')
    list_filter = ('created_at', 'kikoba')
    search_fields = ('title', 'message', 'kikoba__name', 'sender__username') # Assuming sender has a username field

    def get_kikoba_name(self, obj):
        if obj.kikoba:
            return obj.kikoba.name
        return None
    get_kikoba_name.short_description = 'Kikoba'

@admin.register(ScheduledReminder)
class ScheduledReminderAdmin(admin.ModelAdmin):
    list_display = ('get_kikoba_name', 'type', 'frequency', 'is_active')
    list_filter = ('type', 'frequency', 'is_active', 'kikoba')
    search_fields = ('kikoba__name',)

    def get_kikoba_name(self, obj):
        if obj.kikoba:
            return obj.kikoba.name
        return None
    get_kikoba_name.short_description = 'Kikoba'
