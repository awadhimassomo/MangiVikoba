from rest_framework import serializers
from .models import Kikoba, KikobaMembership, KikobaInvitation
from sms.utils import send_sms
from django.contrib.auth import get_user_model

User = get_user_model()

class KikobaSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Kikoba
        fields = (
            'id', 'name', 'description', 'created_by', 'created_by_name', 'created_at', 
            'contribution_frequency', 'interest_rate', 'loan_limit_factor', 
            'loan_term_days', 'late_payment_penalty', 'is_active'
        )
        read_only_fields = ('id', 'created_by', 'created_at')
    
    def get_created_by_name(self, obj):
        return obj.created_by.name

class KikobaMembershipSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    group_name = serializers.SerializerMethodField()
    
    class Meta:
        model = KikobaMembership
        fields = ('id', 'group', 'group_name', 'user', 'user_name', 'role', 'joined_at', 'is_active')
        read_only_fields = ('id', 'joined_at')
    
    def get_user_name(self, obj):
        return obj.user.name
    
    def get_group_name(self, obj):
        return obj.group.name

class KikobaInvitationSerializer(serializers.ModelSerializer):
    kikoba_name = serializers.SerializerMethodField()
    invited_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = KikobaInvitation
        fields = (
            'id', 
            'kikoba', 
            'kikoba_name', 
            'invited_by', 
            'invited_by_name', 
            'email_or_phone', 
            'role', 
            'status', 
            'created_at', 
            'updated_at'
        )
        read_only_fields = ('id', 'invited_by', 'created_at', 'updated_at')
    
    def get_kikoba_name(self, obj):
        return obj.kikoba.name
    
    def get_invited_by_name(self, obj):
        return obj.invited_by.name

class KikobaCreateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=255)
    phone_number = serializers.CharField(max_length=15)

    class Meta:
        model = Kikoba
        fields = (
            'name', 'description', 'contribution_frequency', 'interest_rate',
            'loan_limit_factor', 'loan_term_days', 'late_payment_penalty',
            'is_center_kikoba', 'name', 'phone_number'
        )

    def create(self, validated_data):
        user_name = validated_data.pop('name')
        phone_number = validated_data.pop('phone_number')

        # Create the user
        user = User.objects.create_user(phone_number=phone_number, name=user_name)

        # Create the kikoba
        kikoba = Kikoba.objects.create(created_by=user, **validated_data)

        # Send SMS notification
        message = f"Hongera! Kikoba chako '{kikoba.name}' kimesajiliwa. Namba ya kikoba ni {kikoba.kikoba_number}. Karibu Mangi Vikoba!"
        send_sms(user.phone_number, message)

        return kikoba
