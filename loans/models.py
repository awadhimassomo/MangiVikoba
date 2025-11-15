from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

class LoanProduct(models.Model):
    kikoba = models.ForeignKey('groups.Kikoba', on_delete=models.CASCADE, related_name='loan_products', null=True, blank=True)
    name = models.CharField(max_length=255, help_text=_("e.g., Emergency Loan, Development Loan"))
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, help_text=_("Annual interest rate in percentage, e.g., 10 for 10%"))
    min_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    max_amount = models.DecimalField(max_digits=12, decimal_places=2)
    min_duration_days = models.PositiveIntegerField(default=30, help_text=_("Minimum loan duration in days"))
    max_duration_days = models.PositiveIntegerField(help_text=_("Maximum loan duration in days"))
    grace_period_days = models.PositiveIntegerField(default=0, help_text=_("Grace period in days before first repayment is due"))
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.kikoba.name if self.kikoba else 'General'})"

    class Meta:
        verbose_name = _("Loan Product")
        verbose_name_plural = _("Loan Products")

class LoanApplication(models.Model):
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
        ('withdrawn', _('Withdrawn')),
    ]
    
    PURPOSE_CHOICES = [
        ('business', _('Business')),
        ('education', _('Education')),
        ('medical', _('Medical')),
        ('agriculture', _('Agriculture')),
        ('housing', _('Housing')),
        ('emergency', _('Emergency')),
        ('other', _('Other')),
    ]
    
    # Application Number for tracking
    application_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    
    # Basic Info
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='loan_applications')
    kikoba = models.ForeignKey('groups.Kikoba', on_delete=models.CASCADE, related_name='kikoba_loan_applications')
    loan_product = models.ForeignKey(LoanProduct, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Loan Details
    requested_amount = models.DecimalField(max_digits=12, decimal_places=2)
    purpose = models.CharField(max_length=50, choices=PURPOSE_CHOICES, default='other')
    purpose_description = models.TextField(blank=True, null=True, help_text=_("Detailed purpose description"))
    repayment_period = models.IntegerField(help_text=_("Repayment period in months"), default=12)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, help_text=_("Interest rate in percentage"), default=0.00)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, help_text=_("Total amount including interest"), default=0.00)
    monthly_installment = models.DecimalField(max_digits=12, decimal_places=2, help_text=_("Monthly payment amount"), default=0.00)
    
    # Applicant Details
    applicant_id_number = models.CharField(max_length=100, blank=True, null=True, help_text=_("National ID or voter ID number"))
    applicant_id_photo = models.ImageField(upload_to='loan_applications/ids/', blank=True, null=True)
    applicant_photo = models.ImageField(upload_to='loan_applications/applicants/', blank=True, null=True)
    applicant_signature = models.ImageField(upload_to='loan_applications/signatures/', blank=True, null=True)
    
    # Collateral
    collateral_description = models.TextField(blank=True, null=True, help_text=_("Description of collateral provided"))
    
    # Status & Decision
    application_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    decision_date = models.DateTimeField(null=True, blank=True)
    decision_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='decided_loan_applications')
    remarks = models.TextField(blank=True, null=True, help_text=_("Reason for approval/rejection"))

    def save(self, *args, **kwargs):
        # Generate application number if not exists
        if not self.application_number:
            from django.utils import timezone
            year = timezone.now().year
            # Get the last application number for this year
            last_app = LoanApplication.objects.filter(
                application_number__startswith=f'LN-{year}-'
            ).order_by('-id').first()
            
            if last_app and last_app.application_number:
                last_num = int(last_app.application_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            
            self.application_number = f'LN-{year}-{new_num:05d}'
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.application_number or 'App'} - {self.member.name} - {self.requested_amount} ({self.status})"

    class Meta:
        verbose_name = _("Loan Application")
        verbose_name_plural = _("Loan Applications")
        ordering = ['-application_date']

class Loan(models.Model):
    STATUS_CHOICES = [
        ('pending_disbursement', _('Pending Disbursement')),
        ('active', _('Active')),
        ('paid_on_time', _('Paid on Time')),
        ('late', _('Late')),
        ('defaulted', _('Defaulted')),
        ('cleared_early', _('Cleared Early')),
        ('rescheduled', _('Rescheduled')),
    ]
    application = models.OneToOneField(LoanApplication, on_delete=models.CASCADE, related_name='loan_details', null=True)  # Added null=True
    disbursed_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)  # Added default=0.00
    disbursement_date = models.DateField(null=True, blank=True) # Made nullable
    interest_rate_at_disbursement = models.DecimalField(max_digits=5, decimal_places=2, help_text=_("Interest rate applied at the time of disbursement"), default=0.00) # Added default=0.00
    repayment_schedule_details = models.JSONField(null=True, blank=True, help_text=_("Details of the repayment schedule, e.g., installments, due dates"))
    original_due_date = models.DateField(null=True, blank=True) # Made nullable
    current_due_date = models.DateField(help_text=_("Current due date, may change if rescheduled"), null=True, blank=True) # Added null=True, blank=True
    total_repayable = models.DecimalField(max_digits=12, decimal_places=2, help_text=_("Principal + Interest"), default=0.00) # Added default=0.00
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending_disbursement')
    closed_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Loan for {self.application.member.name} - {self.disbursed_amount} ({self.status})"

    class Meta:
        verbose_name = _("Loan")
        verbose_name_plural = _("Loans")
        ordering = ['-disbursement_date']

class LoanGuarantor(models.Model):
    """Model to store guarantors for loan applications"""
    loan_application = models.ForeignKey(LoanApplication, on_delete=models.CASCADE, related_name='guarantors')
    name = models.CharField(max_length=255, help_text=_("Full name of guarantor"))
    phone_number = models.CharField(max_length=12, help_text=_("Phone number (format: 255XXXXXXXXX)"))
    id_number = models.CharField(max_length=100, help_text=_("National ID or voter ID number"))
    photo = models.ImageField(upload_to='loan_applications/guarantors/', blank=True, null=True)
    signature = models.ImageField(upload_to='loan_applications/guarantor_signatures/', blank=True, null=True)
    guaranteed_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, help_text=_("Amount guaranteed (optional)"))
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='guarantees_given', help_text=_("If guarantor is a kikoba member"))
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - Guarantor for {self.loan_application.application_number}"
    
    class Meta:
        verbose_name = _("Loan Guarantor")
        verbose_name_plural = _("Loan Guarantors")
        ordering = ['created_at']


class Repayment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cash', _('Cash')),
        ('mobile_money', _('Mobile Money')),
        ('bank_transfer', _('Bank Transfer')),
        ('internal_transfer', _('Internal Transfer/Savings Deduction')),
        ('other', _('Other')),
    ]
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='repayments')
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateTimeField(default=timezone.now)
    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHOD_CHOICES, default='cash')
    transaction_reference = models.CharField(max_length=100, blank=True, null=True)
    is_verified = models.BooleanField(default=False, help_text=_("Verified by Kikoba Admin"))
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_repayments')
    verified_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Repayment of {self.amount_paid} for loan {self.loan.id} by {self.loan.application.member.name}"

    class Meta:
        verbose_name = _("Repayment")
        verbose_name_plural = _("Repayments")
        ordering = ['-payment_date']
