from django.shortcuts import render
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Saving, KikobaBalance, MemberBalance
from .serializers import SavingSerializer, KikobaBalanceSerializer, MemberBalanceSerializer
from groups.models import KikobaMembership, Kikoba
from django.utils import timezone
from django.db.models import Q

class IsTreasurerOrChairperson(permissions.BasePermission):
    """
    Custom permission to only allow treasurers or chairpersons to confirm/reject savings.
    """
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Check if user is treasurer or chairperson in the kikoba
        if isinstance(obj, Saving):
            return KikobaMembership.objects.filter(
                kikoba=obj.group,
                user=request.user,
                role__in=['treasurer', 'chairperson', 'kikoba_admin'],
                is_active=True
            ).exists()
        return False

class SavingViewSet(viewsets.ModelViewSet):
    serializer_class = SavingSerializer
    permission_classes = [permissions.IsAuthenticated, IsTreasurerOrChairperson]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['member__name', 'notes', 'transaction_reference']
    ordering_fields = ['transaction_date', 'amount', 'status']
    ordering = ['-transaction_date']
    
    def get_queryset(self):
        user = self.request.user
        
        # Admins (treasurers, chairpersons, kikoba_admins) can see all savings for their vikoba
        admin_vikoba = KikobaMembership.objects.filter(
            user=user, 
            role__in=['treasurer', 'chairperson', 'kikoba_admin'],
            is_active=True
        ).values_list('kikoba', flat=True)
        
        # Regular users can only see their own savings
        return Saving.objects.filter(
            Q(group__in=admin_vikoba) | Q(member=user)
        )
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        saving = self.get_object()
        
        if saving.status != 'pending':
            return Response(
                {'error': 'Only pending savings can be confirmed'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        saving.confirm(request.user)
        
        # Update member balance
        member_balance, created = MemberBalance.objects.get_or_create(
            group=saving.group,
            member=saving.member
        )
        member_balance.update_balance()
        
        # Update kikoba balance
        kikoba_balance, created = KikobaBalance.objects.get_or_create(kikoba=saving.group)
        kikoba_balance.update_balance()
        
        serializer = self.get_serializer(saving)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        saving = self.get_object()
        
        if saving.status != 'pending':
            return Response(
                {'error': 'Only pending savings can be rejected'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        saving.reject(request.user)
        serializer = self.get_serializer(saving)
        return Response(serializer.data)

class KikobaBalanceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = KikobaBalanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Get vikoba where user is a member
        user_vikoba = KikobaMembership.objects.filter(
            user=user,
            is_active=True
        ).values_list('kikoba', flat=True)
        
        return KikobaBalance.objects.filter(kikoba__in=user_vikoba)

class MemberBalanceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MemberBalanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        kikoba_id = self.request.query_params.get('kikoba')
        
        # Check if user is an admin in this kikoba
        is_admin = KikobaMembership.objects.filter(
            user=user,
            kikoba_id=kikoba_id,
            role__in=['chairperson', 'treasurer', 'kikoba_admin'],
            is_active=True
        ).exists()
        
        if is_admin and kikoba_id:
            # Admins can see all member balances in their kikoba
            return MemberBalance.objects.filter(group_id=kikoba_id)
        else:
            # Regular users can only see their own balances
            return MemberBalance.objects.filter(member=user)
