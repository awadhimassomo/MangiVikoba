from django import forms
from registration.models import User
from loans.models import Loan 
from groups.models import Kikoba # Changed from Group
from .models import PolicyLink

class AddMemberForm(forms.Form):
    name = forms.CharField(
        max_length=255, 
        required=True, 
        widget=forms.TextInput(attrs={'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-bright-red focus:border-bright-red sm:text-sm'})
    )
    phone_number = forms.CharField(
        max_length=15, 
        required=True, 
        widget=forms.TextInput(attrs={'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-bright-red focus:border-bright-red sm:text-sm'})
    )
    email = forms.EmailField(
        max_length=255, 
        required=False, 
        widget=forms.EmailInput(attrs={'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-bright-red focus:border-bright-red sm:text-sm'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-bright-red focus:border-bright-red sm:text-sm'}), 
        required=True
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-bright-red focus:border-bright-red sm:text-sm'}), 
        required=True, 
        label="Confirm Password"
    )

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if User.objects.filter(phone_number=phone_number).exists():
            raise forms.ValidationError("A user with this phone number already exists.")
        return phone_number

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")
        return cleaned_data

class AddLoanForm(forms.ModelForm):
    borrower = forms.ModelChoiceField(
        queryset=User.objects.none(), 
        widget=forms.Select(attrs={'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-bright-red focus:border-bright-red sm:text-sm'}),
        empty_label="Select a Borrower"
    )
    amount = forms.DecimalField(
        max_digits=10, 
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-bright-red focus:border-bright-red sm:text-sm', 'step': '0.01'})
    )
    interest_rate = forms.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        label="Interest Rate (%)",
        widget=forms.NumberInput(attrs={'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-bright-red focus:border-bright-red sm:text-sm', 'step': '0.01'})
    )
    term_days = forms.IntegerField(
        label="Loan Term (days)",
        widget=forms.NumberInput(attrs={'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-bright-red focus:border-bright-red sm:text-sm'})
    )
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-bright-red focus:border-bright-red sm:text-sm', 'rows': 3})
    )

    class Meta:
        model = Loan
        fields = ['borrower', 'amount', 'interest_rate', 'term_days', 'reason']

    def __init__(self, *args, **kwargs):
        admin_kikoba = kwargs.pop('admin_kikoba', None) # Changed from admin_group
        super().__init__(*args, **kwargs)
        
        if 'group' in self.fields: # 'group' is the actual field name in Loan model
            del self.fields['group']
        elif 'kikoba' in self.fields: # In case it was already changed to kikoba
            del self.fields['kikoba']

        if admin_kikoba:
            # Include ALL active kikoba members regardless of role (including chairpersons, treasurers, etc.)
            self.fields['borrower'].queryset = User.objects.filter(
                user_kikoba_memberships__kikoba=admin_kikoba,
                user_kikoba_memberships__is_active=True
            ).distinct()
        else:
            self.fields['borrower'].queryset = User.objects.none()

        self.fields['borrower'].label_from_instance = lambda obj: f"{obj.name} ({obj.phone_number})"

class PolicyLinkForm(forms.ModelForm):
    class Meta:
        model = PolicyLink
        fields = ['title', 'url', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'url': forms.URLInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
