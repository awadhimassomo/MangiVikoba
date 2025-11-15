from django.contrib import admin
from .models import PolicyLink
from .admin_models import (
    Investment, InvestmentParticipation, SystemConfiguration,
    SystemNotification, AuditLog
)

# Register your models here.

@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'investment_type', 'status', 'target_amount', 'current_amount', 'start_date', 'end_date']
    list_filter = ['status', 'investment_type', 'risk_level']
    search_fields = ['title', 'description']
    date_hierarchy = 'created_at'

@admin.register(InvestmentParticipation)
class InvestmentParticipationAdmin(admin.ModelAdmin):
    list_display = ['investment', 'kikoba', 'amount_invested', 'status', 'invested_at']
    list_filter = ['status']
    search_fields = ['investment__title', 'kikoba__name']

@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'updated_by', 'updated_at']
    search_fields = ['key', 'value', 'description']

@admin.register(SystemNotification)
class SystemNotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'priority', 'send_to_all', 'is_sent', 'scheduled_for', 'created_by']
    list_filter = ['priority', 'is_sent', 'send_to_all']
    search_fields = ['title', 'message']

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'action', 'model_name', 'description']
    list_filter = ['action', 'model_name']
    search_fields = ['description', 'user__name']
    date_hierarchy = 'timestamp'
    readonly_fields = ['timestamp', 'user', 'action', 'model_name', 'object_id', 'description', 'ip_address']

# Register your models here.
admin.site.register(PolicyLink)
