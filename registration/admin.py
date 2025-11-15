from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

class UserAdmin(BaseUserAdmin):
    list_display = ('phone_number', 'name', 'email', 'role', 'nida_number', 'phone_number_verified', 'verification_status', 'is_active', 'is_staff')
    list_filter = ('is_active', 'role', 'phone_number_verified', 'verification_status')
    fieldsets = (
        (None, {'fields': ('phone_number',)}),
        ('Personal info', {'fields': ('name', 'email', 'profile_photo')}),
        ('Identity & Verification', {'fields': ('nida_number', 'phone_number_verified', 'verification_method', 'verification_status')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'role', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'name', 'email', 'role', 'nida_number', 'profile_photo'),
        }),
    )
    search_fields = ('phone_number', 'name', 'email', 'nida_number')
    ordering = ('phone_number',)
    filter_horizontal = ('groups', 'user_permissions',)
    readonly_fields = ('last_login', 'date_joined',) # user_identifier is auto-generated

admin.site.register(User, UserAdmin)
