from rest_framework import serializers
from .models import Report, ProfitDistribution, MemberProfit
from groups.serializers import KikobaSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class UserMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'name', 'phone_number')

class ReportSerializer(serializers.ModelSerializer):
    group_name = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Report
        fields = (
            'id', 'group', 'group_name', 'user', 'user_name', 'report_type', 
            'period', 'start_date', 'end_date', 'format', 'generated_at', 'file'
        )
        read_only_fields = ('id', 'generated_at', 'file')
    
    def get_group_name(self, obj):
        return obj.group.name if obj.group else None
    
    def get_user_name(self, obj):
        if obj.user:
            return obj.user.name
        return None

class MemberProfitSerializer(serializers.ModelSerializer):
    member_name = serializers.SerializerMethodField()
    
    class Meta:
        model = MemberProfit
        fields = ('id', 'member', 'member_name', 'total_contribution', 'contribution_percentage', 'profit_amount')
    
    def get_member_name(self, obj):
        return obj.member.name if obj.member else None

class ProfitDistributionSerializer(serializers.ModelSerializer):
    group_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    member_profits = MemberProfitSerializer(many=True, read_only=True)
    
    class Meta:
        model = ProfitDistribution
        fields = (
            'id', 'group', 'group_name', 'cycle_start_date', 'cycle_end_date', 
            'total_profit', 'distributed_date', 'created_by', 'created_by_name', 
            'is_finalized', 'notes', 'member_profits'
        )
        read_only_fields = ('id', 'created_by', 'distributed_date', 'member_profits')
    
    def get_group_name(self, obj):
        return obj.group.name if obj.group else None
    
    def get_created_by_name(self, obj):
        return obj.created_by.name if obj.created_by else None
