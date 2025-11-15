from django.db import models
from django.conf import settings
from django.utils import timezone
from groups.models import Kikoba # Add this import


class Report(models.Model):
    TYPE_CHOICES = (
        ('member_statement', 'Member Statement'),
        ('group_financial', 'Group Financial Report'),
        ('profit_distribution', 'Profit Distribution Report'),
    )
    
    PERIOD_CHOICES = (
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annual', 'Annual'),
        ('custom', 'Custom Period'),
    )
    
    FORMAT_CHOICES = (
        ('pdf', 'PDF'),
        ('csv', 'CSV'),
    )
    
    kikoba = models.ForeignKey(Kikoba, on_delete=models.CASCADE, related_name='reports', null=True, blank=True) # Added kikoba field
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='generated_reports', null=True, blank=True)
    report_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    format = models.CharField(max_length=5, choices=FORMAT_CHOICES, default='pdf')
    generated_at = models.DateTimeField(default=timezone.now)
    file = models.FileField(upload_to='reports/', null=True, blank=True)
    
    def __str__(self):
        if self.kikoba:
            return f"{self.get_report_type_display()} for {self.kikoba.name} ({self.start_date} to {self.end_date})"
        return f"{self.get_report_type_display()} ({self.start_date} to {self.end_date})"

class ProfitDistribution(models.Model):
    kikoba = models.ForeignKey(Kikoba, on_delete=models.CASCADE, related_name='profit_distributions', null=True, blank=True) # Added kikoba field
   
    cycle_start_date = models.DateField()
    cycle_end_date = models.DateField()
    total_profit = models.DecimalField(max_digits=12, decimal_places=2)
    distributed_date = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_distributions')
    is_finalized = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        if self.kikoba:
            return f"Profit Distribution for {self.kikoba.name} ({self.cycle_start_date} to {self.cycle_end_date})"
        return f"Profit Distribution ({self.cycle_start_date} to {self.cycle_end_date})"

class MemberProfit(models.Model):
    distribution = models.ForeignKey(ProfitDistribution, on_delete=models.CASCADE, related_name='member_profits')
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profits')
    total_contribution = models.DecimalField(max_digits=12, decimal_places=2)
    contribution_percentage = models.DecimalField(max_digits=5, decimal_places=2)  # Percentage of total group savings
    profit_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    def __str__(self):
        if self.distribution.kikoba:
            return f"{self.member.name}'s profit in {self.distribution.kikoba.name}: {self.profit_amount}"
        return f"{self.member.name}'s profit: {self.profit_amount}"
