from django import forms
from .models import (
    KikobaContributionConfig, Kikoba, KikobaMembership,
    EntryFeePayment, EntryFeeInstallment, ShareContribution,
    ShareInstallment, Saving, EmergencyFundContribution
)

class KikobaContributionConfigForm(forms.ModelForm):
    class Meta:
        model = KikobaContributionConfig
        fields = [
            'entry_fee_amount', 'entry_fee_due_days',
            'share_amount', 'share_frequency', 'share_due_day',
            'emergency_fund_amount', 'emergency_fund_required',
            'min_saving_amount', 'max_saving_amount'
        ]
        widgets = {
            'entry_fee_amount': forms.NumberInput(attrs={'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-bright-red focus:border-bright-red sm:text-sm'}),
            'entry_fee_due_days': forms.NumberInput(attrs={'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-bright-red focus:border-bright-red sm:text-sm'}),
            'share_amount': forms.NumberInput(attrs={'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-bright-red focus:border-bright-red sm:text-sm'}),
            'share_frequency': forms.Select(attrs={'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-bright-red focus:border-bright-red sm:text-sm'}),
            'share_due_day': forms.NumberInput(attrs={'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-bright-red focus:border-bright-red sm:text-sm'}),
            'emergency_fund_amount': forms.NumberInput(attrs={'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-bright-red focus:border-bright-red sm:text-sm'}),
            'emergency_fund_required': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-bright-red border-gray-300 rounded focus:ring-bright-red'}),
            'min_saving_amount': forms.NumberInput(attrs={'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-bright-red focus:border-bright-red sm:text-sm'}),
            'max_saving_amount': forms.NumberInput(attrs={'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-bright-red focus:border-bright-red sm:text-sm'}),
        }
        help_texts = {
            'share_due_day': 'Day of the period (e.g., month or week) when shares are due. Leave blank if not applicable.',
            'emergency_fund_required': 'Check if contributions to the emergency fund are mandatory for members.',
        }

class EntryFeePaymentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        kikoba = kwargs.pop('kikoba', None)
        super().__init__(*args, **kwargs)
        if kikoba:
            self.fields['kikoba_membership'].queryset = KikobaMembership.objects.filter(kikoba=kikoba, is_active=True)
        elif self.instance and hasattr(self.instance, 'kikoba_membership') and self.instance.kikoba_membership:
            # If an instance is provided, ensure its kikoba's members are the choices
            self.fields['kikoba_membership'].queryset = KikobaMembership.objects.filter(kikoba=self.instance.kikoba_membership.kikoba, is_active=True)
        else:
            # Fallback to empty or all if no kikoba context, though ideally kikoba should always be provided
            self.fields['kikoba_membership'].queryset = KikobaMembership.objects.none()

    class Meta:
        model = EntryFeePayment
        fields = ['kikoba_membership', 'amount_due', 'amount_paid', 'due_date']
        widgets = {
            'kikoba_membership': forms.Select(attrs={'class': 'form-control'}),
            'amount_due': forms.NumberInput(attrs={'class': 'form-control'}),
            'amount_paid': forms.NumberInput(attrs={'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class EntryFeeInstallmentForm(forms.ModelForm):
    class Meta:
        model = EntryFeeInstallment
        fields = ['entry_fee_payment', 'amount']
        widgets = {
            'entry_fee_payment': forms.HiddenInput(), # Usually pre-filled in the view
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class ShareContributionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        kikoba = kwargs.pop('kikoba', None)
        super().__init__(*args, **kwargs)
        if kikoba:
            self.fields['kikoba_membership'].queryset = KikobaMembership.objects.filter(kikoba=kikoba, is_active=True)
        elif self.instance and hasattr(self.instance, 'kikoba_membership') and self.instance.kikoba_membership:
            self.fields['kikoba_membership'].queryset = KikobaMembership.objects.filter(kikoba=self.instance.kikoba_membership.kikoba, is_active=True)
        else:
            self.fields['kikoba_membership'].queryset = KikobaMembership.objects.none()

    class Meta:
        model = ShareContribution
        fields = ['kikoba_membership', 'amount_due', 'amount_paid', 'period_start', 'period_end', 'due_date']
        widgets = {
            'kikoba_membership': forms.Select(attrs={'class': 'form-control'}),
            'amount_due': forms.NumberInput(attrs={'class': 'form-control'}),
            'amount_paid': forms.NumberInput(attrs={'class': 'form-control'}),
            'period_start': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'period_end': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class ShareInstallmentForm(forms.ModelForm):
    class Meta:
        model = ShareInstallment
        fields = ['share_contribution', 'amount']
        widgets = {
            'share_contribution': forms.HiddenInput(), # Usually pre-filled in the view
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class SavingForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        kikoba = kwargs.pop('kikoba', None)
        super().__init__(*args, **kwargs)
        if kikoba:
            self.fields['kikoba_membership'].queryset = KikobaMembership.objects.filter(kikoba=kikoba, is_active=True)
        elif self.instance and hasattr(self.instance, 'kikoba_membership') and self.instance.kikoba_membership:
            self.fields['kikoba_membership'].queryset = KikobaMembership.objects.filter(kikoba=self.instance.kikoba_membership.kikoba, is_active=True)
        else:
            self.fields['kikoba_membership'].queryset = KikobaMembership.objects.none()

    class Meta:
        model = Saving
        fields = ['kikoba_membership', 'amount']
        widgets = {
            'kikoba_membership': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class EmergencyFundContributionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        kikoba = kwargs.pop('kikoba', None)
        super().__init__(*args, **kwargs)
        if kikoba:
            self.fields['kikoba_membership'].queryset = KikobaMembership.objects.filter(kikoba=kikoba, is_active=True)
        elif self.instance and hasattr(self.instance, 'kikoba_membership') and self.instance.kikoba_membership:
            self.fields['kikoba_membership'].queryset = KikobaMembership.objects.filter(kikoba=self.instance.kikoba_membership.kikoba, is_active=True)
        else:
            self.fields['kikoba_membership'].queryset = KikobaMembership.objects.none()

    class Meta:
        model = EmergencyFundContribution
        fields = ['kikoba_membership', 'amount']
        widgets = {
            'kikoba_membership': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
        }
