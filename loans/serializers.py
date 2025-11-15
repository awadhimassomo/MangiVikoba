from rest_framework import serializers
from .models import Loan, Repayment, LoanApplication, LoanProduct # Added LoanApplication, LoanProduct
from groups.serializers import KikobaSerializer # Assuming this exists and is relevant
from django.contrib.auth import get_user_model
from django.utils import timezone
from groups.models import Kikoba, KikobaMembership
from django.db.models import Sum

User = get_user_model()

class UserMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'name', 'phone_number', 'user_identifier')

class LoanProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanProduct
        fields = '__all__'

class LoanApplicationSerializer(serializers.ModelSerializer):
    member = UserMinimalSerializer(read_only=True)
    kikoba = KikobaSerializer(read_only=True) # Or a simpler KikobaMinimalSerializer
    loan_product = LoanProductSerializer(read_only=True)
    decision_by = UserMinimalSerializer(read_only=True)

    # Fields for creating/updating an application
    kikoba_id = serializers.PrimaryKeyRelatedField(
        queryset=Kikoba.objects.all(), source='kikoba', write_only=True
    )
    loan_product_id = serializers.PrimaryKeyRelatedField(
        queryset=LoanProduct.objects.all(), source='loan_product', write_only=True
    )

    class Meta:
        model = LoanApplication
        fields = (
            'id', 'member', 'kikoba', 'kikoba_id', 'loan_product', 'loan_product_id', 
            'requested_amount', 'purpose', 'application_date', 'status', 
            'decision_date', 'decision_by', 'remarks'
        )
        read_only_fields = ('id', 'application_date', 'status', 'decision_date', 'decision_by')

    def validate_kikoba_id(self, value):
        request = self.context.get('request')
        if request and hasattr(request, "user"):
            if not KikobaMembership.objects.filter(user=request.user, kikoba=value, is_active=True).exists():
                raise serializers.ValidationError("You are not an active member of the selected Kikoba.")
        return value

class LoanSerializer(serializers.ModelSerializer):
    # Using LoanApplicationSerializer for the 'application' field for detailed view
    application = LoanApplicationSerializer(read_only=True)
    total_paid = serializers.SerializerMethodField()
    remaining_balance = serializers.SerializerMethodField()

    class Meta:
        model = Loan
        fields = (
            'id', 'application', 'disbursed_amount', 'disbursement_date',
            'interest_rate_at_disbursement', 'repayment_schedule_details',
            'original_due_date', 'current_due_date', 'total_repayable', 'status',
            'closed_date', 'total_paid', 'remaining_balance'
        )
        read_only_fields = ('id', 'disbursement_date', 'status', 'closed_date', 'total_paid', 'remaining_balance')

    def get_total_paid(self, obj):
        return obj.repayments.aggregate(total=Sum('amount_paid'))['total'] or 0

    def get_remaining_balance(self, obj):
        return obj.total_repayable - self.get_total_paid(obj)

class RepaymentSerializer(serializers.ModelSerializer): # Renamed from LoanRepaymentSerializer
    # loan = LoanSerializer(read_only=True) # Avoid deep nesting if loan details are not always needed
    loan_id = serializers.PrimaryKeyRelatedField(
        queryset=Loan.objects.all(), source='loan', write_only=True
    )
    verified_by = UserMinimalSerializer(read_only=True)
    member_name = serializers.CharField(source='loan.application.member.name', read_only=True)
    kikoba_name = serializers.CharField(source='loan.application.kikoba.name', read_only=True)

    class Meta:
        model = Repayment # Changed from LoanRepayment
        fields = (
            'id', 'loan', 'loan_id', 'member_name', 'kikoba_name', 'amount_paid', 'payment_date', 
            'payment_method', 'transaction_reference', 'is_verified', 
            'verified_by', 'verified_at', 'notes'
        )
        read_only_fields = ('id', 'payment_date', 'verified_at', 'member_name', 'kikoba_name')

    def create(self, validated_data):
        # 'loan' instance is expected to be passed in validated_data or context by the view
        # If loan_id is used, the view should fetch the loan instance and pass it.
        # For example, if loan is in context (as done in LoanViewSet.record_repayment):
        if 'loan' not in validated_data and self.context.get('loan'):
            validated_data['loan'] = self.context['loan']
        
        # If user is in context, can be used for verified_by if logic allows self-verification or auto-verification
        # request_user = self.context.get('request').user
        # if validated_data.get('is_verified') and not validated_data.get('verified_by'):
        # validated_data['verified_by'] = request_user
        # validated_data['verified_at'] = timezone.now()
        
        return super().create(validated_data)
