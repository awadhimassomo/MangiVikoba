from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
import logging

logger = logging.getLogger(__name__)
from groups.models import (
    Kikoba, KikobaMembership, KikobaInvitation, 
    KikobaContributionConfig, EntryFeePayment, 
    ShareContribution, EmergencyFundContribution
)
from savings.models import Saving, KikobaBalance, MemberBalance, SavingCycle, Contribution
from loans.models import LoanProduct, LoanApplication, Loan, Repayment, LoanGuarantor
from notifications.models import Notification

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom token serializer that accepts phone_number instead of username
    Since the User model uses phone_number as USERNAME_FIELD, we need to
    explicitly set the username_field to tell JWT to use phone_number.
    """
    username_field = User.USERNAME_FIELD
    
    def validate(self, attrs):
        print("\n=== LOGIN ATTEMPT ===")
        print(f"Received data in serializer: {attrs}")
        print(f"Username field: {self.username_field}")
        print(f"User model USERNAME_FIELD: {User.USERNAME_FIELD}")
        print(f"Available fields in serializer: {list(self.fields.keys())}")
        
        try:
            data = super().validate(attrs)
            print(f"✓ Login successful for: {attrs.get(self.username_field)}")
            return data
        except Exception as e:
            print(f"✗ Login failed: {str(e)}")
            print(f"✗ Error type: {type(e).__name__}")
            import traceback
            print(f"✗ Full traceback:")
            traceback.print_exc()
            raise


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    class Meta:
        model = User
        fields = [
            'id', 'phone_number', 'name', 'email', 'role', 
            'nida_number', 'phone_number_verified', 'profile_photo',
            'verification_method', 'verification_status', 'date_joined',
            'is_active'
        ]
        read_only_fields = ['id', 'date_joined', 'is_active']
        extra_kwargs = {
            'password': {'write_only': True}
        }


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, min_length=6)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['phone_number', 'name', 'email', 'password', 'password_confirm', 'role']
        
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords do not match")
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user


class KikobaContributionConfigSerializer(serializers.ModelSerializer):
    """Serializer for Kikoba contribution configuration"""
    class Meta:
        model = KikobaContributionConfig
        fields = '__all__'


class KikobaSerializer(serializers.ModelSerializer):
    """Serializer for Kikoba (Group) model"""
    created_by_name = serializers.CharField(source='created_by.name', read_only=True)
    member_count = serializers.SerializerMethodField()
    contribution_config = KikobaContributionConfigSerializer(read_only=True)
    
    class Meta:
        model = Kikoba
        fields = [
            'id', 'name', 'description', 'created_by', 'created_by_name',
            'created_at', 'contribution_frequency', 'interest_rate',
            'loan_limit_factor', 'loan_term_days', 'late_payment_penalty',
            'is_active', 'is_center_kikoba', 'location', 'estimated_members',
            'kikoba_number', 'member_count', 'contribution_config',
            'constitution_document', 'other_documents', 'creator_phone_number'
        ]
        read_only_fields = ['id', 'created_at', 'kikoba_number', 'created_by']
    
    def get_member_count(self, obj):
        return obj.kikoba_memberships.filter(is_active=True).count()


class KikobaMembershipSerializer(serializers.ModelSerializer):
    """Serializer for Kikoba membership"""
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_phone = serializers.CharField(source='user.phone_number', read_only=True)
    kikoba_name = serializers.CharField(source='kikoba.name', read_only=True)
    
    class Meta:
        model = KikobaMembership
        fields = [
            'id', 'kikoba', 'kikoba_name', 'user', 'user_name', 
            'user_phone', 'role', 'joined_at', 'is_active'
        ]
        read_only_fields = ['id', 'joined_at']


class KikobaInvitationSerializer(serializers.ModelSerializer):
    """Serializer for Kikoba invitations"""
    kikoba_name = serializers.CharField(source='kikoba.name', read_only=True)
    invited_by_name = serializers.CharField(source='invited_by.name', read_only=True)
    
    class Meta:
        model = KikobaInvitation
        fields = [
            'id', 'kikoba', 'kikoba_name', 'phone_number', 
            'invited_by', 'invited_by_name', 'status', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SavingSerializer(serializers.ModelSerializer):
    """Serializer for Saving transactions"""
    member_name = serializers.CharField(source='member.name', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    confirmed_by_name = serializers.CharField(source='confirmed_by.name', read_only=True, allow_null=True)
    
    class Meta:
        model = Saving
        fields = [
            'id', 'group', 'group_name', 'member', 'member_name',
            'amount', 'transaction_date', 'status', 'confirmed_by',
            'confirmed_by_name', 'confirmation_date', 'transaction_reference', 'notes'
        ]
        read_only_fields = ['id', 'transaction_date', 'confirmed_by', 'confirmation_date']


class ContributionSerializer(serializers.ModelSerializer):
    """Serializer for Contribution model"""
    member_name = serializers.CharField(source='member.name', read_only=True)
    kikoba_name = serializers.CharField(source='kikoba.name', read_only=True)
    
    class Meta:
        model = Contribution
        fields = [
            'id', 'member', 'member_name', 'kikoba', 'kikoba_name',
            'saving_cycle', 'amount', 'date_contributed', 
            'transaction_reference', 'is_verified', 'verified_by', 'verified_at'
        ]
        read_only_fields = ['id', 'date_contributed', 'verified_by', 'verified_at']


class KikobaBalanceSerializer(serializers.ModelSerializer):
    """Serializer for Kikoba balance"""
    kikoba_name = serializers.CharField(source='kikoba.name', read_only=True)
    
    class Meta:
        model = KikobaBalance
        fields = [
            'id', 'kikoba', 'kikoba_name', 'total_savings',
            'total_loans', 'available_balance', 'last_updated'
        ]
        read_only_fields = ['id', 'last_updated']


class MemberBalanceSerializer(serializers.ModelSerializer):
    """Serializer for Member balance"""
    member_name = serializers.CharField(source='member.name', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    
    class Meta:
        model = MemberBalance
        fields = [
            'id', 'group', 'group_name', 'member', 'member_name',
            'total_contribution', 'last_contribution'
        ]
        read_only_fields = ['id', 'last_contribution']


class SavingCycleSerializer(serializers.ModelSerializer):
    """Serializer for Saving Cycle"""
    kikoba_name = serializers.CharField(source='kikoba.name', read_only=True)
    
    class Meta:
        model = SavingCycle
        fields = [
            'id', 'kikoba', 'kikoba_name', 'name', 
            'start_date', 'end_date', 'is_active', 'description'
        ]
        read_only_fields = ['id']


class LoanProductSerializer(serializers.ModelSerializer):
    """Serializer for Loan Product"""
    kikoba_name = serializers.CharField(source='kikoba.name', read_only=True, allow_null=True)
    
    class Meta:
        model = LoanProduct
        fields = [
            'id', 'kikoba', 'kikoba_name', 'name', 'interest_rate',
            'min_amount', 'max_amount', 'min_duration_days',
            'max_duration_days', 'grace_period_days', 'is_active', 'description'
        ]
        read_only_fields = ['id']


class LoanGuarantorSerializer(serializers.ModelSerializer):
    """Serializer for Loan Guarantor"""
    photo_url = serializers.SerializerMethodField()
    signature_url = serializers.SerializerMethodField()
    
    class Meta:
        model = LoanGuarantor
        fields = [
            'id', 'name', 'phone_number', 'id_number', 
            'photo', 'photo_url', 'signature', 'signature_url',
            'guaranteed_amount', 'member'
        ]
        read_only_fields = ['id']
    
    def get_photo_url(self, obj):
        if obj.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return None
    
    def get_signature_url(self, obj):
        if obj.signature:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.signature.url)
            return obj.signature.url
        return None


class LoanApplicationSerializer(serializers.ModelSerializer):
    """Serializer for Loan Application"""
    member_name = serializers.CharField(source='member.name', read_only=True)
    member_phone = serializers.CharField(source='member.phone_number', read_only=True)
    kikoba_name = serializers.CharField(source='kikoba.name', read_only=True)
    loan_product_name = serializers.CharField(source='loan_product.name', read_only=True, allow_null=True)
    decision_by_name = serializers.CharField(source='decision_by.name', read_only=True, allow_null=True)
    guarantors = LoanGuarantorSerializer(many=True, read_only=True)
    
    # URL fields for images
    applicant_id_photo_url = serializers.SerializerMethodField()
    applicant_photo_url = serializers.SerializerMethodField()
    applicant_signature_url = serializers.SerializerMethodField()
    
    class Meta:
        model = LoanApplication
        fields = [
            'id', 'application_number', 'member', 'member_name', 'member_phone',
            'kikoba', 'kikoba_name', 'loan_product', 'loan_product_name',
            'requested_amount', 'purpose', 'purpose_description', 'repayment_period',
            'interest_rate', 'total_amount', 'monthly_installment',
            'applicant_id_number', 'applicant_id_photo', 'applicant_id_photo_url',
            'applicant_photo', 'applicant_photo_url', 'applicant_signature', 'applicant_signature_url',
            'collateral_description', 'guarantors',
            'application_date', 'status', 'decision_date',
            'decision_by', 'decision_by_name', 'remarks'
        ]
        read_only_fields = ['id', 'application_number', 'application_date', 'decision_date', 'decision_by', 'status']
    
    def get_applicant_id_photo_url(self, obj):
        if obj.applicant_id_photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.applicant_id_photo.url)
            return obj.applicant_id_photo.url
        return None
    
    def get_applicant_photo_url(self, obj):
        if obj.applicant_photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.applicant_photo.url)
            return obj.applicant_photo.url
        return None
    
    def get_applicant_signature_url(self, obj):
        if obj.applicant_signature:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.applicant_signature.url)
            return obj.applicant_signature.url
        return None


class LoanApplicationCreateSerializer(serializers.Serializer):
    """Serializer for creating loan applications via API"""
    kikundi = serializers.IntegerField(required=True, help_text="Vikoba/Group ID")
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=True, min_value=0.01)
    purpose = serializers.ChoiceField(
        choices=['business', 'education', 'medical', 'agriculture', 'housing', 'emergency', 'other'],
        required=True
    )
    purpose_description = serializers.CharField(required=False, allow_blank=True)
    repayment_period = serializers.IntegerField(required=True, min_value=1, max_value=24)
    applicant_id_number = serializers.CharField(required=True, max_length=100)
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2, required=True, min_value=0)
    total_amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=True, min_value=0)
    monthly_installment = serializers.DecimalField(max_digits=12, decimal_places=2, required=True, min_value=0)
    collateral_description = serializers.CharField(required=False, allow_blank=True)
    
    # Images
    applicant_id_photo = serializers.ImageField(required=False, allow_null=True)
    applicant_photo = serializers.ImageField(required=False, allow_null=True)
    
    # Guarantors
    guarantors = serializers.ListField(
        child=serializers.DictField(),
        required=True,
        min_length=1,
        help_text="List of guarantor objects"
    )
    
    def validate_guarantors(self, value):
        """Validate guarantors list"""
        if not value:
            raise serializers.ValidationError("At least one guarantor is required")
        
        for idx, guarantor in enumerate(value):
            if 'name' not in guarantor or not guarantor['name']:
                raise serializers.ValidationError(f"Guarantor {idx + 1}: name is required")
            if 'phone_number' not in guarantor or not guarantor['phone_number']:
                raise serializers.ValidationError(f"Guarantor {idx + 1}: phone_number is required")
            if 'id_number' not in guarantor or not guarantor['id_number']:
                raise serializers.ValidationError(f"Guarantor {idx + 1}: id_number is required")
            
            # Validate phone number format
            phone = guarantor['phone_number']
            if not phone.startswith('255') or len(phone) != 12:
                raise serializers.ValidationError(
                    f"Guarantor {idx + 1}: phone_number must be in format 255XXXXXXXXX (12 digits)"
                )
        
        return value
    
    def validate_kikundi(self, value):
        """Validate that kikundi exists"""
        from groups.models import Kikoba
        if not Kikoba.objects.filter(id=value).exists():
            raise serializers.ValidationError("Kikundi/Vikoba does not exist")
        return value
    
    def create(self, validated_data):
        """Create loan application with guarantors"""
        from groups.models import Kikoba
        
        guarantors_data = validated_data.pop('guarantors')
        kikundi_id = validated_data.pop('kikundi')
        amount = validated_data.pop('amount')
        
        # Get the kikoba
        kikoba = Kikoba.objects.get(id=kikundi_id)
        
        # Create loan application
        loan_app = LoanApplication.objects.create(
            member=self.context['request'].user,
            kikoba=kikoba,
            requested_amount=amount,
            purpose=validated_data['purpose'],
            purpose_description=validated_data.get('purpose_description', ''),
            repayment_period=validated_data['repayment_period'],
            applicant_id_number=validated_data['applicant_id_number'],
            interest_rate=validated_data['interest_rate'],
            total_amount=validated_data['total_amount'],
            monthly_installment=validated_data['monthly_installment'],
            collateral_description=validated_data.get('collateral_description', ''),
            applicant_id_photo=validated_data.get('applicant_id_photo'),
            applicant_photo=validated_data.get('applicant_photo'),
        )
        
        # Create guarantors
        for guarantor_data in guarantors_data:
            LoanGuarantor.objects.create(
                loan_application=loan_app,
                name=guarantor_data['name'],
                phone_number=guarantor_data['phone_number'],
                id_number=guarantor_data['id_number'],
            )
        
        return loan_app


class LoanSerializer(serializers.ModelSerializer):
    """Serializer for Loan"""
    member_name = serializers.CharField(source='application.member.name', read_only=True)
    kikoba_name = serializers.CharField(source='application.kikoba.name', read_only=True)
    
    class Meta:
        model = Loan
        fields = [
            'id', 'application', 'member_name', 'kikoba_name',
            'disbursed_amount', 'disbursement_date', 
            'interest_rate_at_disbursement', 'repayment_schedule_details',
            'original_due_date', 'current_due_date', 'total_repayable',
            'status', 'closed_date'
        ]
        read_only_fields = ['id', 'disbursement_date', 'closed_date']


class RepaymentSerializer(serializers.ModelSerializer):
    """Serializer for Loan Repayment"""
    loan_member_name = serializers.CharField(source='loan.application.member.name', read_only=True)
    verified_by_name = serializers.CharField(source='verified_by.name', read_only=True, allow_null=True)
    
    class Meta:
        model = Repayment
        fields = [
            'id', 'loan', 'loan_member_name', 'amount_paid',
            'payment_date', 'payment_method', 'transaction_reference',
            'is_verified', 'verified_by', 'verified_by_name', 
            'verified_at', 'notes'
        ]
        read_only_fields = ['id', 'payment_date', 'verified_by', 'verified_at']


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notifications"""
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class EntryFeePaymentSerializer(serializers.ModelSerializer):
    """Serializer for Entry Fee Payments"""
    member_name = serializers.CharField(source='kikoba_membership.user.name', read_only=True)
    kikoba_name = serializers.CharField(source='kikoba_membership.kikoba.name', read_only=True)
    
    class Meta:
        model = EntryFeePayment
        fields = [
            'id', 'kikoba_membership', 'member_name', 'kikoba_name',
            'amount_due', 'amount_paid', 'is_fully_paid', 'due_date'
        ]
        read_only_fields = ['id', 'amount_paid', 'is_fully_paid']


class ShareContributionSerializer(serializers.ModelSerializer):
    """Serializer for Share Contributions"""
    member_name = serializers.CharField(source='kikoba_membership.user.name', read_only=True)
    kikoba_name = serializers.CharField(source='kikoba_membership.kikoba.name', read_only=True)
    
    class Meta:
        model = ShareContribution
        fields = [
            'id', 'kikoba_membership', 'member_name', 'kikoba_name',
            'amount_due', 'amount_paid', 'is_fully_paid', 'due_date',
            'period_start', 'period_end'
        ]
        read_only_fields = ['id', 'amount_paid', 'is_fully_paid']


class EmergencyFundContributionSerializer(serializers.ModelSerializer):
    """Serializer for Emergency Fund Contributions"""
    member_name = serializers.CharField(source='kikoba_membership.user.name', read_only=True)
    kikoba_name = serializers.CharField(source='kikoba_membership.kikoba.name', read_only=True)
    
    class Meta:
        model = EmergencyFundContribution
        fields = [
            'id', 'kikoba_membership', 'member_name', 'kikoba_name',
            'amount', 'contributed_on'
        ]
        read_only_fields = ['id', 'contributed_on']
