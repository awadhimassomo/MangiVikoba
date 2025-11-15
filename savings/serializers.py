from rest_framework import serializers
from .models import Saving, KikobaBalance, MemberBalance
from django.contrib.auth import get_user_model

User = get_user_model()

class UserMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'name', 'phone_number')

class SavingSerializer(serializers.ModelSerializer):
    member_name = serializers.SerializerMethodField()
    group_name = serializers.SerializerMethodField()
    confirmed_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Saving
        fields = (
            'id', 'group', 'group_name', 'member', 'member_name', 'amount', 
            'transaction_date', 'status', 'confirmed_by', 'confirmed_by_name',
            'confirmation_date', 'transaction_reference', 'notes'
        )
        read_only_fields = ('id', 'confirmed_by', 'confirmation_date', 'status')
    
    def get_member_name(self, obj):
        return obj.member.name
    
    def get_group_name(self, obj):
        return obj.group.name 
    
    def get_confirmed_by_name(self, obj):
        if obj.confirmed_by:
            return obj.confirmed_by.name
        return None
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['member'] = user
        return super().create(validated_data)

class KikobaBalanceSerializer(serializers.ModelSerializer):
    kikoba_name = serializers.SerializerMethodField()

    class Meta:
        model = KikobaBalance
        fields = ('id', 'kikoba', 'kikoba_name', 'total_balance', 'last_updated')

    def get_kikoba_name(self, obj):
        return obj.kikoba.name

class MemberBalanceSerializer(serializers.ModelSerializer):
    member = UserMinimalSerializer()
    group_name = serializers.SerializerMethodField()
    
    class Meta:
        model = MemberBalance
        fields = ('id', 'group', 'group_name', 'member', 'total_contribution', 'last_contribution')
    
    def get_group_name(self, obj):
        return obj.group.name
