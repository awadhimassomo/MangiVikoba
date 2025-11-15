from django.contrib import admin
from .models import LoanProduct, LoanApplication, Loan, Repayment
from django.utils import timezone

@admin.register(LoanProduct)
class LoanProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'kikoba', 'interest_rate', 'min_amount', 'max_amount', 'min_duration_days', 'max_duration_days', 'is_active')
    list_filter = ('is_active', 'kikoba__name', 'interest_rate')
    search_fields = ('name', 'kikoba__name')
    autocomplete_fields = ['kikoba']

@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = ('member', 'kikoba', 'loan_product', 'requested_amount', 'status', 'application_date')
    list_filter = ('status', 'kikoba__name', 'loan_product__name', 'application_date')
    search_fields = ('member__name', 'kikoba__name', 'loan_product__name')
    readonly_fields = ('decision_date',)
    autocomplete_fields = ['member', 'kikoba', 'loan_product', 'decision_by']
    date_hierarchy = 'application_date'
    actions = ['approve_applications', 'reject_applications']

    def approve_applications(self, request, queryset):
        for app in queryset.filter(status='pending'):
            app.status = 'approved'
            app.decision_by = request.user
            app.decision_date = timezone.now()
            app.save()
    approve_applications.short_description = "Approve selected pending applications"

    def reject_applications(self, request, queryset):
        for app in queryset.filter(status='pending'):
            app.status = 'rejected'
            app.decision_by = request.user
            app.decision_date = timezone.now()
            app.save()
    reject_applications.short_description = "Reject selected pending applications"

@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('application_member', 'kikoba_name', 'disbursed_amount', 'status', 'disbursement_date', 'current_due_date', 'total_repayable')
    list_filter = ('status', 'disbursement_date', 'current_due_date', 'application__kikoba__name')
    search_fields = ('application__member__name', 'application__kikoba__name', 'application__loan_product__name')
    readonly_fields = ('closed_date',)
    autocomplete_fields = ['application']
    date_hierarchy = 'disbursement_date'

    @admin.display(description='Member', ordering='application__member__name')
    def application_member(self, obj):
        return obj.application.member.name

    @admin.display(description='Kikoba', ordering='application__kikoba__name')
    def kikoba_name(self, obj):
        return obj.application.kikoba.name

@admin.register(Repayment)
class RepaymentAdmin(admin.ModelAdmin):
    list_display = ('loan_applicant_name', 'loan_kikoba_name', 'amount_paid', 'payment_date', 'payment_method', 'is_verified')
    list_filter = ('is_verified', 'payment_method', 'payment_date', 'loan__application__kikoba__name')
    search_fields = ('loan__application__member__name', 'loan__application__kikoba__name', 'transaction_reference')
    autocomplete_fields = ['loan', 'verified_by']
    readonly_fields = ('verified_at',)
    date_hierarchy = 'payment_date'
    actions = ['mark_repayments_as_verified']

    @admin.display(description='Applicant', ordering='loan__application__member__name')
    def loan_applicant_name(self, obj):
        return obj.loan.application.member.name

    @admin.display(description='Kikoba', ordering='loan__application__kikoba__name')
    def loan_kikoba_name(self, obj):
        return obj.loan.application.kikoba.name

    def mark_repayments_as_verified(self, request, queryset):
        queryset.update(is_verified=True, verified_by=request.user, verified_at=timezone.now())
    mark_repayments_as_verified.short_description = "Mark selected repayments as verified"
