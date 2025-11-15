from django.contrib import admin
from .models import SavingCycle, Contribution
from django.utils import timezone

@admin.register(SavingCycle)
class SavingCycleAdmin(admin.ModelAdmin):
    list_display = ('name', 'kikoba', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active', 'kikoba__name', 'start_date')
    search_fields = ('name', 'kikoba__name')
    date_hierarchy = 'start_date'

@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = ('member', 'kikoba', 'amount', 'date_contributed', 'saving_cycle', 'is_verified', 'verified_by')
    list_filter = ('is_verified', 'kikoba__name', 'member__name', 'date_contributed', 'saving_cycle__name')
    search_fields = ('member__name', 'kikoba__name', 'transaction_reference', 'saving_cycle__name')
    autocomplete_fields = ['member', 'kikoba', 'saving_cycle', 'verified_by']
    readonly_fields = ('verified_at',)
    date_hierarchy = 'date_contributed'

    actions = ['mark_as_verified']

    def mark_as_verified(self, request, queryset):
        queryset.update(is_verified=True, verified_by=request.user, verified_at=timezone.now())
    mark_as_verified.short_description = "Mark selected contributions as verified"
