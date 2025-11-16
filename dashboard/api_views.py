from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, NumberFilter, CharFilter, ChoiceFilter, DateFilter
from django.db.models import Q, F, Sum, Count, Case, When, Value, IntegerField, DecimalField
from django.utils import timezone
from datetime import timedelta, datetime
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404

from loans.models import Loan, Repayment, LoanApplication
from savings.models import Saving, Contribution
from groups.models import Kikoba
from registration.models import User

from .api_serializers import (
    LoanSerializer, RepaymentSerializer, 
    SavingSerializer, ContributionSerializer,
    EmergencyFundSerializer, ShareContributionSerializer,
    UserSerializer, KikobaSerializer
)

from .admin_models import Investment
from .serializers import InvestmentSerializer

# Base filter classes
class KikobaFilterMixin:
    def get_queryset(self):
        queryset = super().get_queryset()
        kikoba_id = self.request.query_params.get('kikoba_id')
        if kikoba_id:
            queryset = queryset.filter(kikoba_id=kikoba_id)
        return queryset

class DateRangeFilterMixin:
    def get_queryset(self):
        queryset = super().get_queryset()
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            try:
                start_date = timezone.make_aware(datetime.strptime(start_date, '%Y-%m-%d'))
                queryset = queryset.filter(created_at__gte=start_date)
            except ValueError:
                pass
                
        if end_date:
            try:
                end_date = timezone.make_aware(datetime.strptime(end_date, '%Y-%m-%d'))
                end_date = end_date + timedelta(days=1)  # Include the entire end date
                queryset = queryset.filter(created_at__lte=end_date)
            except ValueError:
                pass
                
        return queryset

# Investment Views
class InvestmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows investments to be viewed or edited.
    """
    queryset = Investment.objects.all().order_by('-created_at')
    serializer_class = InvestmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'status': ['exact', 'in'],
        'investment_type': ['exact', 'in'],
        'risk_level': ['exact'],
        'available_to_all_vikoba': ['exact'],
        'created_at': ['gte', 'lte', 'exact', 'gt', 'lt'],
        'start_date': ['gte', 'lte', 'exact', 'gt', 'lt'],
        'end_date': ['gte', 'lte', 'exact', 'gt', 'lt'],
    }
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['created_at', 'start_date', 'end_date', 'target_amount', 'current_amount']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Optionally filter by status, investment_type, or search query
        """
        queryset = super().get_queryset()
        
        # Additional filtering
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status__in=status_param.split(','))
            
        investment_type = self.request.query_params.get('investment_type')
        if investment_type:
            queryset = queryset.filter(investment_type__in=investment_type.split(','))
            
        return queryset
        
    def get_serializer_context(self):
        """
        Extra context provided to the serializer class.
        """
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    @action(detail=True, methods=['get'])
    def details(self, request, pk=None):
        """
        Get detailed information about a specific investment
        """
        investment = self.get_object()
        serializer = self.get_serializer(investment)
        return Response(serializer.data)
