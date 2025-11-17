from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid
from django.utils.translation import gettext_lazy as _

class Kikoba(models.Model): # Renamed from Group
    GROUP_TYPE_CHOICES = (
        ('standard', 'Standard VIKOBA (Variable-Share ASCA)'),
        ('fixed_share', 'Fixed-Share VIKOBA'),
        ('interest_refund', 'Interest Refund VIKOBA'),
        ('rosca', 'ROSCA (Rotating Savings)'),
        ('welfare', 'Welfare/Help Group (WCG)'),
    )
    
    FREQUENCY_CHOICES = (
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-weekly'),
        ('monthly', 'Monthly'),
    )
    
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    # Changed related_name to 'created_vikoba'
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_vikoba') 
    created_at = models.DateTimeField(auto_now_add=True)
    contribution_frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, default='monthly')
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    loan_limit_factor = models.DecimalField(max_digits=5, decimal_places=2, default=3.00)
    loan_term_days = models.PositiveIntegerField(default=90)
    late_payment_penalty = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    is_active = models.BooleanField(default=True)
    is_center_kikoba = models.BooleanField(default=False, help_text=_('Can new members join this Kikoba directly from a central registration form?'))
    location = models.CharField(max_length=255, blank=True, null=True, help_text=_('Physical location or address of the Kikoba.'))
    ESTIMATED_MEMBERS_CHOICES = [
        ('2-5', '2-5 Members'),
        ('6-10', '6-10 Members'),
        ('11-20', '11-20 Members'),
        ('21-50', '21-50 Members'),
        ('51-100', '51-100 Members'),
        ('101-200', '101-200 Members'),
        ('201-500', '201-500 Members'),
        ('501-1000', '501-1000 Members'),
        ('1000+', '1000+ Members'),
    ]
    estimated_members = models.CharField(
        max_length=20,
        choices=ESTIMATED_MEMBERS_CHOICES,
        blank=True,
        null=True,
        help_text=_('Estimated number of members in the Kikoba.')
    )
    constitution_document = models.FileField(
        upload_to='kikoba_documents/constitutions/',
        null=True,
        blank=True,
        help_text=_("Upload the Kikoba's constitution document (optional).")
    )
    other_documents = models.FileField(
        upload_to='kikoba_documents/others/',
        null=True,
        blank=True,
        help_text=_('Upload any other relevant documents for the Kikoba (optional).')
    )
    kikoba_number = models.CharField(
        max_length=15,
        unique=True,
        blank=True,
        help_text=_('Unique identification number for the Kikoba.')
    )
    group_type = models.CharField(
        max_length=20,
        choices=GROUP_TYPE_CHOICES,
        null=True,  # Allow null for existing records
        blank=True,  # Allow blank in forms for existing records
        help_text=_('Type of the group which determines the financial model used.')
    )
    creator_phone_number = models.CharField(max_length=15, blank=True, null=True, help_text=_('Phone number of the user who initiated creation.'))
    
    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.kikoba_number:
            last_kikoba = Kikoba.objects.all().order_by('id').last()
            if last_kikoba and last_kikoba.kikoba_number and last_kikoba.kikoba_number.startswith('KB'):
                try:
                    last_num = int(last_kikoba.kikoba_number[2:])
                    new_num = last_num + 1
                    self.kikoba_number = f"KB{new_num:06d}"
                except ValueError:
                    self.kikoba_number = f"KB{uuid.uuid4().hex[:6].upper()}"
            else:
                self.kikoba_number = "KB000001"
            while Kikoba.objects.filter(kikoba_number=self.kikoba_number).exclude(pk=self.pk).exists():
                if self.kikoba_number.startswith('KB') and len(self.kikoba_number) > 2:
                    try:
                        current_num_part = int(self.kikoba_number[2:])
                        self.kikoba_number = f"KB{current_num_part + 1:06d}"
                    except ValueError:
                        self.kikoba_number = f"KB{uuid.uuid4().hex[:6].upper()}"
                else:
                    self.kikoba_number = f"KB{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

class KikobaMembership(models.Model): # Renamed from GroupMembership
    ROLE_CHOICES = (
        ('member', 'Member'),
        ('chairperson', 'Chairperson'),
        ('treasurer', 'Treasurer'),
        ('secretary', 'Secretary'),
        ('kikoba_admin', 'Kikoba Admin'),
        ('accountant', 'Accountant'),  # For managing loans and financial reports
    )
    
    # Changed ForeignKey to Kikoba and related_name
    kikoba = models.ForeignKey(Kikoba, on_delete=models.CASCADE, related_name='kikoba_memberships') 
    # Changed related_name
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_kikoba_memberships') 
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        # Each user can have only ONE role per Kikoba
        # Leadership roles (chairperson, treasurer, secretary) are still members
        unique_together = ('kikoba', 'user')
    
    def __str__(self):
        return f"{self.user.name} - {self.kikoba.name} ({self.get_role_display()})"

class KikobaInvitation(models.Model): # Renamed from GroupInvitation
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )
    
    # Renamed field from group to kikoba and updated related_name
    kikoba = models.ForeignKey(Kikoba, on_delete=models.CASCADE, related_name='kikoba_invitations') 
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_kikoba_invitations') # Updated related_name
    email_or_phone = models.CharField(max_length=255) 
    invitation_code = models.CharField(max_length=20, unique=True, blank=True, help_text='Unique invitation code (e.g., WA-123456)')
    role = models.CharField(max_length=15, choices=KikobaMembership.ROLE_CHOICES, default='member')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.invitation_code:
            # Generate unique code with Kikoba prefix
            import random
            import string
            
            # Get first 2 letters of Kikoba name (uppercase)
            prefix = self.kikoba.name[:2].upper()
            
            # Generate 6-digit random number
            while True:
                code_number = ''.join(random.choices(string.digits, k=6))
                code = f"{prefix}-{code_number}"
                
                # Check if code already exists
                if not KikobaInvitation.objects.filter(invitation_code=code).exists():
                    self.invitation_code = code
                    break
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Invitation {self.invitation_code} for {self.email_or_phone} to {self.kikoba.name}" # Updated to self.kikoba.name

# Consider renaming this model to KikobaInvitation if it's actively used.
# For now, I've updated its ForeignKey to Kikoba.

class KikobaContributionConfig(models.Model):
    kikoba = models.OneToOneField(Kikoba, on_delete=models.CASCADE, related_name='contribution_config')
    
    entry_fee_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    entry_fee_due_days = models.PositiveIntegerField(default=30, help_text="Days to pay entry fee from joining")
    
    share_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    share_frequency = models.CharField(max_length=10, choices=Kikoba.FREQUENCY_CHOICES, default='monthly')
    share_due_day = models.PositiveIntegerField(null=True, blank=True, help_text="Day of period shares are due")
    
    emergency_fund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    emergency_fund_required = models.BooleanField(default=False)
    
    min_saving_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_saving_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"Contribution Config for {self.kikoba.name}"

class KikobaMemberPayment(models.Model):
    kikoba_membership = models.ForeignKey(KikobaMembership, on_delete=models.CASCADE)
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_fully_paid = models.BooleanField(default=False)
    due_date = models.DateField(null=True, blank=True)
    
    class Meta:
        abstract = True

    def __str__(self):
        return f"Payment for {self.kikoba_membership.user.name} in {self.kikoba_membership.kikoba.name}"

class EntryFeePayment(KikobaMemberPayment):
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('mobile_money', 'Mobile Money'),
        ('bank_transfer', 'Bank Transfer'),
        ('check', 'Check'),
        ('other', 'Other'),
    ]
    
    payment_date = models.DateTimeField(null=True, blank=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash')
    notes = models.TextField(blank=True, null=True)
    
    def update_payment_status(self):
        self.is_fully_paid = self.amount_paid >= self.amount_due
        self.save()

    def __str__(self):
        return f"Entry Fee for {self.kikoba_membership.user.name} - Due: {self.amount_due}"

class EntryFeeInstallment(models.Model):
    entry_fee_payment = models.ForeignKey(EntryFeePayment, on_delete=models.CASCADE, related_name='installments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_on = models.DateField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        payment = self.entry_fee_payment
        payment.amount_paid = payment.installments.aggregate(total=models.Sum('amount'))['total'] or 0
        payment.is_fully_paid = payment.amount_paid >= payment.amount_due
        payment.save()

    def __str__(self):
        return f"Installment of {self.amount} for {self.entry_fee_payment}"

class ShareContribution(KikobaMemberPayment):
    period_start = models.DateField()
    period_end = models.DateField()

    def __str__(self):
        return f"Share for {self.kikoba_membership.user.name} ({self.period_start} to {self.period_end})"
    
class ShareInstallment(models.Model):
    share_contribution = models.ForeignKey(ShareContribution, on_delete=models.CASCADE, related_name='installments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_on = models.DateField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        contribution = self.share_contribution
        contribution.amount_paid = contribution.installments.aggregate(total=models.Sum('amount'))['total'] or 0
        contribution.is_fully_paid = contribution.amount_paid >= contribution.amount_due
        contribution.save()

    def __str__(self):
        return f"Share Installment of {self.amount} for {self.share_contribution}"

class Saving(models.Model):
    kikoba_membership = models.ForeignKey(KikobaMembership, on_delete=models.CASCADE, related_name='savings')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    saved_on = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Saving by {self.kikoba_membership.user.name} of {self.amount} on {self.saved_on}"

class EmergencyFundContribution(models.Model):
    kikoba_membership = models.ForeignKey(KikobaMembership, on_delete=models.CASCADE, related_name='emergency_fund_contributions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    contributed_on = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Emergency Fund by {self.kikoba_membership.user.name} of {self.amount} on {self.contributed_on}"
