from rest_framework import serializers
from loans.models import Loan, LoanApplication, Repayment
from savings.models import Saving, Contribution
from groups.models import Kikoba
from registration.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'phone_number', 'member_id']

class KikobaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Kikoba
        fields = ['id', 'name', 'registration_number', 'created_at']

class LoanSerializer(serializers.ModelSerializer):
    borrower = UserSerializer(read_only=True)
    kikoba = KikobaSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Loan
        fields = [
            'id', 'loan_id', 'borrower', 'kikoba', 'amount', 'interest_rate', 'term_months',
            'purpose', 'status', 'status_display', 'issue_date', 'due_date', 'created_at',
            'total_repayment_amount', 'amount_paid', 'remaining_balance'
        ]

class RepaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Repayment
        fields = ['id', 'loan', 'amount', 'payment_date', 'payment_method', 'receipt_number', 'notes']

class SavingSerializer(serializers.ModelSerializer):
    member = UserSerializer(read_only=True)
    kikoba = KikobaSerializer(read_only=True, source='group')
    
    class Meta:
        model = Saving
        fields = ['id', 'member', 'kikoba', 'amount', 'transaction_date', 'transaction_reference', 'status', 'notes', 'created_at']

class ContributionSerializer(serializers.ModelSerializer):
    member = UserSerializer(read_only=True)
    kikoba = KikobaSerializer(read_only=True, source='kikoba')
    
    class Meta:
        model = Contribution
        fields = ['id', 'member', 'kikoba', 'amount', 'date_contributed', 'transaction_reference', 'is_verified', 'verified_by', 'verified_at']

class EmergencyFundSerializer(serializers.ModelSerializer):
    member = UserSerializer(read_only=True)
    kikoba = KikobaSerializer(read_only=True, source='group')
    
    class Meta:
        model = Saving
        fields = [
            'id', 'member', 'kikoba', 'amount', 'transaction_date', 'status',
            'transaction_reference', 'notes', 'confirmed_by', 'confirmation_date'
        ]

class ShareContributionSerializer(serializers.ModelSerializer):
    member = UserSerializer(read_only=True)
    kikoba = KikobaSerializer(read_only=True, source='group')
    
    class Meta:
        model = Contribution
        fields = [
            'id', 'member', 'kikoba', 'amount', 'date_contributed', 
            'transaction_reference', 'is_verified', 'verified_by', 'verified_at'
        ]
