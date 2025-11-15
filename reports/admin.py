from django.contrib import admin
from .models import Report, ProfitDistribution, MemberProfit

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('report_type', 'get_kikoba_name', 'period', 'start_date', 'end_date', 'generated_at')
    list_filter = ('report_type', 'period', 'generated_at', 'kikoba__name') # Changed 'kikoba' to 'kikoba__name'
    search_fields = ('kikoba__name',)

    def get_kikoba_name(self, obj):
        if obj.kikoba:
            return obj.kikoba.name
        return None
    get_kikoba_name.short_description = 'Kikoba'

@admin.register(ProfitDistribution)
class ProfitDistributionAdmin(admin.ModelAdmin):
    list_display = ('get_kikoba_name', 'cycle_start_date', 'cycle_end_date', 'total_profit', 'is_finalized')
    list_filter = ('is_finalized', 'kikoba__name') # Changed 'kikoba' to 'kikoba__name'
    search_fields = ('kikoba__name',)

    def get_kikoba_name(self, obj):
        if obj.kikoba:
            return obj.kikoba.name
        return None
    get_kikoba_name.short_description = 'Kikoba'

@admin.register(MemberProfit)
class MemberProfitAdmin(admin.ModelAdmin):
    list_display = ('member', 'distribution', 'total_contribution', 'contribution_percentage', 'profit_amount')
    search_fields = ('member__username', 'distribution__kikoba__name') # Assuming member has a username field
