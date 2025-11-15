from django.shortcuts import render
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Report, ProfitDistribution, MemberProfit
from .serializers import ReportSerializer, ProfitDistributionSerializer, MemberProfitSerializer
from groups.models import Kikoba, KikobaMembership
from savings.models import MemberBalance
from loans.models import Loan
from django.db.models import Sum, F, ExpressionWrapper, DecimalField, Q
from django.utils import timezone
from decimal import Decimal
import csv
import io
from django.http import HttpResponse
# PDF generation libraries
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

class IsKikobaAdmin(permissions.BasePermission):
    """
    Custom permission to only allow kikoba admins to perform certain actions.
    """
    def has_object_permission(self, request, view, obj):
        # Check if user is an admin in the kikoba
        if hasattr(obj, 'group'): # Assuming obj.group is the kikoba instance
            return KikobaMembership.objects.filter( # MODIFIED: Changed from GroupMembership
                kikoba=obj.group, # MODIFIED: Changed from group to kikoba
                user=request.user,
                role__in=['chairperson', 'treasurer', 'kikoba_admin'], # MODIFIED: Added kikoba_admin
                is_active=True
            ).exists()
        return False

class ReportViewSet(viewsets.ModelViewSet):
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['generated_at']
    ordering = ['-generated_at']
    
    def get_queryset(self):
        user = self.request.user
        
        # Get vikoba where user is a member
        user_vikoba = KikobaMembership.objects.filter( # MODIFIED: Changed from GroupMembership
            user=user,
            is_active=True
        ).values_list('kikoba', flat=True) # MODIFIED: Changed from group to kikoba
        
        # Assuming Report.group refers to a Kikoba instance
        return Report.objects.filter(
            Q(group__in=user_vikoba) | Q(user=user)
        )
    
    def perform_create(self, serializer):
        report = serializer.save(user=self.request.user)
        
        # Generate the report file based on type and format
        self.generate_report_file(report)
    
    def generate_report_file(self, report):
        """Generate a report file based on type and format"""
        if report.report_type == 'member_statement':
            if report.format == 'pdf':
                self.generate_member_statement_pdf(report)
            else:  # CSV
                self.generate_member_statement_csv(report)
        elif report.report_type == 'group_financial':
            if report.format == 'pdf':
                self.generate_group_financial_pdf(report)
            else:  # CSV
                self.generate_group_financial_csv(report)
        elif report.report_type == 'profit_distribution':
            if report.format == 'pdf':
                self.generate_profit_distribution_pdf(report)
            else:  # CSV
                self.generate_profit_distribution_csv(report)
    
    def generate_member_statement_pdf(self, report):
        # TODO: Generate PDF file for member statement
        pass
    
    def generate_member_statement_csv(self, report):
        # TODO: Generate CSV file for member statement
        pass
    
    def generate_group_financial_pdf(self, report):
        # TODO: Generate PDF file for group financial report
        pass
    
    def generate_group_financial_csv(self, report):
        # TODO: Generate CSV file for group financial report
        pass
    
    def generate_profit_distribution_pdf(self, report):
        # TODO: Generate PDF file for profit distribution report
        pass
    
    def generate_profit_distribution_csv(self, report):
        # TODO: Generate CSV file for profit distribution report
        pass

class ProfitDistributionViewSet(viewsets.ModelViewSet):
    serializer_class = ProfitDistributionSerializer
    permission_classes = [permissions.IsAuthenticated, IsKikobaAdmin] # MODIFIED: Renamed IsGroupAdmin
    
    def get_queryset(self):
        user = self.request.user
        
        # Get vikoba where user is an admin
        admin_vikoba = KikobaMembership.objects.filter( # MODIFIED: Changed from GroupMembership
            user=user,
            role__in=['chairperson', 'treasurer', 'kikoba_admin'], # MODIFIED: Added kikoba_admin
            is_active=True
        ).values_list('kikoba', flat=True) # MODIFIED: Changed from group to kikoba
        
        # Assuming ProfitDistribution.group refers to a Kikoba instance
        return ProfitDistribution.objects.filter(group__in=admin_vikoba)
    
    def perform_create(self, serializer):
        profit_distribution = serializer.save(
            created_by=self.request.user,
            distributed_date=timezone.now()
        )
        
        if not profit_distribution.is_finalized:
            # Calculate profit distribution
            self.calculate_profit_distribution(profit_distribution)
    
    @action(detail=True, methods=['post'])
    def finalize(self, request, pk=None):
        distribution = self.get_object()
        
        if distribution.is_finalized:
            return Response(
                {'error': 'Distribution is already finalized'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update the distribution
        distribution.is_finalized = True
        distribution.save()
        
        # TODO: Create notifications for members about their profit
        
        serializer = self.get_serializer(distribution)
        return Response(serializer.data)
    
    def calculate_profit_distribution(self, distribution):
        """Calculate profit distribution based on member contributions"""
        kikoba = distribution.group # This is a Kikoba instance
        start_date = distribution.cycle_start_date
        end_date = distribution.cycle_end_date
        
        # Get all active members with contributions in this kikoba
        members = MemberBalance.objects.filter(
            group=kikoba, # Ensure MemberBalance.group refers to Kikoba
            total_contribution__gt=0
        )
        
        # Calculate total group contribution
        total_contribution = members.aggregate(
            total=Sum('total_contribution')
        )['total'] or Decimal('0.00')
        
        if total_contribution <= 0:
            return
        
        # For each member, calculate their percentage and profit amount
        for member_balance in members:
            percentage = (member_balance.total_contribution / total_contribution) * 100
            profit_amount = (percentage / 100) * distribution.total_profit
            
            # Create or update MemberProfit
            MemberProfit.objects.create(
                distribution=distribution,
                member=member_balance.member,
                total_contribution=member_balance.total_contribution,
                contribution_percentage=percentage,
                profit_amount=profit_amount
            )
