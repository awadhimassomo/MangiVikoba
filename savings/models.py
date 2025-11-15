from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

class Saving(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('rejected', 'Rejected'),
    )
    
    group = models.ForeignKey('groups.Kikoba', on_delete=models.CASCADE, related_name='savings')  # Changed Group to Kikoba
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='savings')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='confirmed_savings'
    )
    confirmation_date = models.DateTimeField(null=True, blank=True)
    transaction_reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.member.name} saved {self.amount} in {self.group.name}"
    
    def confirm(self, confirmed_by):
        self.status = 'confirmed'
        self.confirmed_by = confirmed_by
        self.confirmation_date = timezone.now()
        self.save()
    
    def reject(self, confirmed_by):
        self.status = 'rejected'
        self.confirmed_by = confirmed_by
        self.confirmation_date = timezone.now()
        self.save()

class KikobaBalance(models.Model): # Renamed from GroupBalance
    """This model tracks the total balance of a kikoba at any given time"""
    kikoba = models.OneToOneField('groups.Kikoba', on_delete=models.CASCADE, related_name='kikoba_balance_detail') # Renamed from group, updated related_name
    total_savings = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_loans = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    available_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    last_updated = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.kikoba.name} Balance: {self.available_balance}" # Changed to self.kikoba.name
    
    def update_balance(self):
        """Recalculate the kikoba balance"""
        from loans.models import Loan
        
        total_savings = Saving.objects.filter(
            group=self.kikoba, # Changed from self.group
            status='confirmed'
        ).aggregate(models.Sum('amount'))['amount__sum'] or 0
        
        total_loans = Loan.objects.filter(
            group=self.kikoba, # Changed from self.group
            status__in=['approved', 'partially_paid']
        ).aggregate(
            models.Sum(models.F('amount') - models.F('amount_paid'))
        )['amount__sum'] or 0
        
        self.total_savings = total_savings
        self.total_loans = total_loans
        self.available_balance = total_savings - total_loans
        self.last_updated = timezone.now()
        self.save()

class MemberBalance(models.Model):
    """This model tracks each member's total contribution to a kikoba"""
    group = models.ForeignKey('groups.Kikoba', on_delete=models.CASCADE, related_name='member_balances')  # Changed Group to Kikoba
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='balances')
    total_contribution = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    last_contribution = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('group', 'member')
    
    def __str__(self):
        return f"{self.member.name} contribution in {self.group.name}: {self.total_contribution}"
    
    def update_balance(self):
        """Recalculate the member's total contribution"""
        total = Saving.objects.filter(
            group=self.group,
            member=self.member,
            status='confirmed'
        ).aggregate(models.Sum('amount'))['amount__sum'] or 0
        
        last_saving = Saving.objects.filter(
            group=self.group,
            member=self.member,
            status='confirmed'
        ).order_by('-transaction_date').first()
        
        self.total_contribution = total
        if last_saving:
            self.last_contribution = last_saving.transaction_date
        self.save()

class SavingCycle(models.Model):
    kikoba = models.ForeignKey('groups.Kikoba', on_delete=models.CASCADE, related_name='saving_cycles')
    name = models.CharField(max_length=255, help_text=_("e.g., Q1 2024 Savings Cycle"))
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.kikoba.name} - {self.name}"

    class Meta:
        verbose_name = _("Saving Cycle")
        verbose_name_plural = _("Saving Cycles")
        ordering = ['-start_date']

class Contribution(models.Model):
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='contributions')
    kikoba = models.ForeignKey('groups.Kikoba', on_delete=models.CASCADE, related_name='kikoba_contributions')
    saving_cycle = models.ForeignKey(SavingCycle, on_delete=models.SET_NULL, null=True, blank=True, related_name='cycle_contributions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_contributed = models.DateTimeField(default=timezone.now)
    transaction_reference = models.CharField(max_length=100, blank=True, null=True, help_text=_("Optional reference for the transaction, e.g., M-Pesa code"))
    is_verified = models.BooleanField(default=False, help_text=_("Verified by Kikoba Admin"))
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_contributions')
    verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.member.name} - {self.amount} to {self.kikoba.name}"

    class Meta:
        verbose_name = _("Contribution")
        verbose_name_plural = _("Contributions")
        ordering = ['-date_contributed']
