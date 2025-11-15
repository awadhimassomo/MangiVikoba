from django.contrib import admin
from .models import Kikoba, KikobaMembership, KikobaInvitation, KikobaContributionConfig, EntryFeePayment, EntryFeeInstallment, ShareContribution, ShareInstallment, Saving, EmergencyFundContribution # Changed GroupInvitation to KikobaInvitation

class KikobaAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'created_at', 'contribution_frequency', 'interest_rate', 'is_active', 'is_center_kikoba')
    list_filter = ('is_active', 'is_center_kikoba', 'contribution_frequency')
    search_fields = ('name', 'description', 'created_by__name')
    raw_id_fields = ('created_by',)

class KikobaMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'kikoba', 'role', 'joined_at', 'is_active')
    list_filter = ('is_active', 'role', 'kikoba__name')
    search_fields = ('user__name', 'kikoba__name')
    raw_id_fields = ('user', 'kikoba')

class KikobaInvitationAdmin(admin.ModelAdmin): # Renamed from GroupInvitationAdmin
    list_display = ('email_or_phone', 'kikoba', 'role', 'status', 'invited_by', 'created_at') # Changed group to kikoba
    list_filter = ('status', 'role', 'kikoba__name') # Changed group__name to kikoba__name
    search_fields = ('email_or_phone', 'invited_by__name', 'kikoba__name') # Changed group__name to kikoba__name
    raw_id_fields = ('invited_by', 'kikoba') # Changed group to kikoba

# Register your models here.
admin.site.register(Kikoba, KikobaAdmin) 
admin.site.register(KikobaMembership, KikobaMembershipAdmin) 
admin.site.register(KikobaInvitation, KikobaInvitationAdmin) # Changed GroupInvitation to KikobaInvitation
admin.site.register(KikobaContributionConfig)
admin.site.register(EntryFeePayment)
admin.site.register(EntryFeeInstallment)
admin.site.register(ShareContribution)
admin.site.register(ShareInstallment)
admin.site.register(Saving)
admin.site.register(EmergencyFundContribution)
