from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.reverse import reverse
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from django.db.models import Q, Sum
from django_filters.rest_framework import DjangoFilterBackend
import logging

logger = logging.getLogger(__name__)

from groups.models import (
    Kikoba, KikobaMembership, KikobaInvitation,
    KikobaContributionConfig, EntryFeePayment,
    ShareContribution, EmergencyFundContribution
)
from savings.models import Saving, KikobaBalance, MemberBalance, SavingCycle, Contribution
from loans.models import LoanProduct, LoanApplication, Loan, Repayment
from notifications.models import Notification

from .serializers import (
    UserSerializer, UserRegistrationSerializer,
    CustomTokenObtainPairSerializer,
    KikobaSerializer, KikobaMembershipSerializer, KikobaInvitationSerializer,
    KikobaContributionConfigSerializer, SavingSerializer, ContributionSerializer,
    KikobaBalanceSerializer, MemberBalanceSerializer, SavingCycleSerializer,
    LoanProductSerializer, LoanApplicationSerializer, LoanApplicationCreateSerializer, LoanSerializer,
    RepaymentSerializer, NotificationSerializer, EntryFeePaymentSerializer,
    ShareContributionSerializer, EmergencyFundContributionSerializer, LoanGuarantorSerializer
)

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom token view that uses phone_number instead of username
    """
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        print("\n" + "="*60)
        print("=== TOKEN REQUEST ===")
        print(f"Request method: {request.method}")
        print(f"Request content type: {request.content_type}")
        print(f"Request data: {request.data}")
        print(f"Serializer class: {self.serializer_class}")
        print(f"Expected username field: {self.serializer_class.username_field}")
        print("="*60)
        
        response = super().post(request, *args, **kwargs)
        
        print(f"\nResponse status: {response.status_code}")
        if response.status_code != 200:
            print(f"ERROR - Response data: {response.data}")
        print("="*60 + "\n")
        
        return response


@api_view(['GET'])
@permission_classes([AllowAny])
def api_root(request, format=None):
    """
    MangiVikoba REST API Root
    
    Welcome to the MangiVikoba API. This API provides comprehensive access to:
    - User management
    - Vikoba (savings group) operations
    - Savings and contributions tracking
    - Loan management
    - Notifications
    
    Authentication required for all endpoints except registration and login.
    Use JWT tokens in the Authorization header: Bearer {token}
    """
    return Response({
        'message': 'Welcome to MangiVikoba REST API v1',
        'version': '1.0.0',
        'authentication': {
            'login': reverse('token_obtain_pair', request=request, format=format),
            'refresh': reverse('token_refresh', request=request, format=format),
            'verify': reverse('token_verify', request=request, format=format),
        },
        'endpoints': {
            'users': reverse('user-list', request=request, format=format),
            'vikoba': reverse('kikoba-list', request=request, format=format),
            'memberships': reverse('membership-list', request=request, format=format),
            'invitations': reverse('invitation-list', request=request, format=format),
            'savings': reverse('saving-list', request=request, format=format),
            'contributions': reverse('contribution-list', request=request, format=format),
            'member_balances': reverse('member-balance-list', request=request, format=format),
            'kikoba_balances': reverse('kikoba-balance-list', request=request, format=format),
            'saving_cycles': reverse('saving-cycle-list', request=request, format=format),
            'loan_products': reverse('loan-product-list', request=request, format=format),
            'loan_applications': reverse('loan-application-list', request=request, format=format),
            'loans': reverse('loan-list', request=request, format=format),
            'repayments': reverse('repayment-list', request=request, format=format),
            'notifications': reverse('notification-list', request=request, format=format),
            'entry_fee_payments': reverse('entry-fee-payment-list', request=request, format=format),
            'share_contributions': reverse('share-contribution-list', request=request, format=format),
            'emergency_fund_contributions': reverse('emergency-fund-contribution-list', request=request, format=format),
        },
        'documentation': 'See API_DOCUMENTATION.md for complete reference',
        'note': 'Most endpoints require authentication. Register at /users/ or login at /auth/token/'
    })


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint for users
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'phone_number', 'email']
    ordering_fields = ['date_joined', 'name']
    
    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return super().get_permissions()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegistrationSerializer
        return UserSerializer
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_vikoba(self, request):
        """Get all vikoba where current user is a member"""
        memberships = KikobaMembership.objects.filter(
            user=request.user,
            is_active=True
        ).select_related('kikoba')
        vikoba = [membership.kikoba for membership in memberships]
        serializer = KikobaSerializer(vikoba, many=True)
        return Response(serializer.data)


class KikobaViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Kikoba (Groups)
    """
    queryset = Kikoba.objects.all()
    serializer_class = KikobaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'is_center_kikoba', 'contribution_frequency']
    search_fields = ['name', 'kikoba_number', 'location']
    ordering_fields = ['created_at', 'name']
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """Get all members of a kikoba"""
        kikoba = self.get_object()
        memberships = kikoba.kikoba_memberships.filter(is_active=True)
        serializer = KikobaMembershipSerializer(memberships, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def balance(self, request, pk=None):
        """Get kikoba balance"""
        kikoba = self.get_object()
        try:
            balance = kikoba.kikoba_balance_detail
            balance.update_balance()
            serializer = KikobaBalanceSerializer(balance)
            return Response(serializer.data)
        except KikobaBalance.DoesNotExist:
            return Response(
                {"detail": "Balance not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        """Join a kikoba"""
        kikoba = self.get_object()
        user = request.user
        
        # Check if already a member
        if KikobaMembership.objects.filter(kikoba=kikoba, user=user).exists():
            return Response(
                {"detail": "Already a member"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        membership = KikobaMembership.objects.create(
            kikoba=kikoba,
            user=user,
            role='member'
        )
        serializer = KikobaMembershipSerializer(membership)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class KikobaMembershipViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Kikoba memberships
    """
    queryset = KikobaMembership.objects.all()
    serializer_class = KikobaMembershipSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['kikoba', 'user', 'role', 'is_active']
    ordering_fields = ['joined_at']
    
    def get_queryset(self):
        """Filter to show only memberships for current user or their kikoba"""
        user = self.request.user
        return KikobaMembership.objects.filter(
            Q(user=user) | Q(kikoba__created_by=user)
        )


class KikobaInvitationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Kikoba invitations
    """
    queryset = KikobaInvitation.objects.all()
    serializer_class = KikobaInvitationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['kikoba', 'status']
    ordering_fields = ['created_at']
    
    def perform_create(self, serializer):
        serializer.save(invited_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Accept an invitation"""
        invitation = self.get_object()
        
        if invitation.status != 'pending':
            return Response(
                {"detail": "Invitation already processed"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        invitation.status = 'accepted'
        invitation.save()
        
        # Create membership
        KikobaMembership.objects.create(
            kikoba=invitation.kikoba,
            user=request.user,
            role='member'
        )
        
        return Response({"detail": "Invitation accepted"})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject an invitation"""
        invitation = self.get_object()
        
        if invitation.status != 'pending':
            return Response(
                {"detail": "Invitation already processed"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        invitation.status = 'rejected'
        invitation.save()
        
        return Response({"detail": "Invitation rejected"})


class SavingViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Savings
    """
    queryset = Saving.objects.all()
    serializer_class = SavingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['group', 'member', 'status']
    ordering_fields = ['transaction_date']
    
    def get_queryset(self):
        """Filter savings for user's vikoba"""
        user = self.request.user
        return Saving.objects.filter(
            Q(member=user) | Q(group__memberships__user=user)
        ).distinct()
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirm a saving transaction"""
        saving = self.get_object()
        saving.confirm(confirmed_by=request.user)
        serializer = self.get_serializer(saving)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a saving transaction"""
        saving = self.get_object()
        saving.reject(confirmed_by=request.user)
        serializer = self.get_serializer(saving)
        return Response(serializer.data)


class ContributionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Contributions
    """
    queryset = Contribution.objects.all()
    serializer_class = ContributionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['kikoba', 'member', 'saving_cycle', 'is_verified']
    ordering_fields = ['date_contributed']
    
    def get_queryset(self):
        """Filter contributions for user's vikoba"""
        user = self.request.user
        return Contribution.objects.filter(
            Q(member=user) | Q(kikoba__memberships__user=user)
        ).distinct()


class MemberBalanceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for Member Balances (read-only)
    """
    queryset = MemberBalance.objects.all()
    serializer_class = MemberBalanceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['group', 'member']
    
    def get_queryset(self):
        """Filter balances for user's vikoba"""
        user = self.request.user
        return MemberBalance.objects.filter(
            Q(member=user) | Q(group__memberships__user=user)
        ).distinct()


class KikobaBalanceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for Kikoba Balances (read-only)
    """
    queryset = KikobaBalance.objects.all()
    serializer_class = KikobaBalanceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['kikoba']


class SavingCycleViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Saving Cycles
    """
    queryset = SavingCycle.objects.all()
    serializer_class = SavingCycleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['kikoba', 'is_active']
    ordering_fields = ['start_date']


class LoanProductViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Loan Products
    """
    queryset = LoanProduct.objects.all()
    serializer_class = LoanProductSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['kikoba', 'is_active']
    ordering_fields = ['name']


class LoanApplicationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Loan Applications
    Supports creating, listing, and retrieving loan applications with file uploads
    """
    queryset = LoanApplication.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'kikoba', 'member']
    ordering_fields = ['application_date']
    
    def get_serializer_class(self):
        """Use different serializer for create action"""
        if self.action == 'create':
            return LoanApplicationCreateSerializer
        return LoanApplicationSerializer
    
    def get_queryset(self):
        """Filter applications for user's vikoba or user's own applications"""
        user = self.request.user
        return LoanApplication.objects.filter(
            Q(member=user) | Q(kikoba__memberships__user=user)
        ).select_related('member', 'kikoba', 'loan_product', 'decision_by').prefetch_related('guarantors').distinct()
    
    def create(self, request, *args, **kwargs):
        """
        Create a new loan application with guarantors
        Supports multipart/form-data for file uploads
        """
        import json
        
        # Handle guarantors as JSON string if sent via form-data
        data = request.data.copy()
        if 'guarantors' in data and isinstance(data['guarantors'], str):
            try:
                data['guarantors'] = json.loads(data['guarantors'])
            except json.JSONDecodeError:
                return Response(
                    {'success': False, 'message': 'Invalid guarantors format', 'errors': {'guarantors': ['Must be valid JSON']}},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        serializer = self.get_serializer(data=data)
        
        if not serializer.is_valid():
            return Response(
                {
                    'success': False,
                    'message': 'Validation failed',
                    'errors': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        loan_app = serializer.save()
        
        # Return success response with full application details
        response_serializer = LoanApplicationSerializer(loan_app, context={'request': request})
        
        return Response(
            {
                'success': True,
                'message': 'Loan application submitted successfully',
                'data': response_serializer.data
            },
            status=status.HTTP_201_CREATED
        )
    
    def list(self, request, *args, **kwargs):
        """List loan applications with success wrapper"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve single loan application with success wrapper"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a loan application"""
        from django.utils import timezone
        
        application = self.get_object()
        
        if application.status != 'pending':
            return Response(
                {'success': False, 'message': f'Application is already {application.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        application.status = 'approved'
        application.decision_by = request.user
        application.decision_date = timezone.now()
        application.remarks = request.data.get('remarks', '')
        application.save()
        
        serializer = self.get_serializer(application)
        return Response({
            'success': True,
            'message': 'Loan application approved successfully',
            'data': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a loan application"""
        from django.utils import timezone
        
        application = self.get_object()
        remarks = request.data.get('remarks', '')
        
        if not remarks:
            return Response(
                {'success': False, 'message': 'Validation failed', 'errors': {'remarks': ['Reason for rejection is required']}},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if application.status != 'pending':
            return Response(
                {'success': False, 'message': f'Application is already {application.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        application.status = 'rejected'
        application.decision_by = request.user
        application.decision_date = timezone.now()
        application.remarks = remarks
        application.save()
        
        serializer = self.get_serializer(application)
        return Response({
            'success': True,
            'message': 'Loan application rejected',
            'data': serializer.data
        })


class LoanViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Loans
    """
    queryset = Loan.objects.all()
    serializer_class = LoanSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['disbursement_date']
    
    def get_queryset(self):
        """Filter loans for user's vikoba"""
        user = self.request.user
        return Loan.objects.filter(
            Q(application__member=user) | Q(application__kikoba__memberships__user=user)
        ).distinct()


class RepaymentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Loan Repayments
    """
    queryset = Repayment.objects.all()
    serializer_class = RepaymentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['loan', 'is_verified', 'payment_method']
    ordering_fields = ['payment_date']
    
    def get_queryset(self):
        """Filter repayments for user's loans"""
        user = self.request.user
        return Repayment.objects.filter(
            Q(loan__application__member=user) | 
            Q(loan__application__kikoba__memberships__user=user)
        ).distinct()
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify a repayment"""
        from django.utils import timezone
        
        repayment = self.get_object()
        repayment.is_verified = True
        repayment.verified_by = request.user
        repayment.verified_at = timezone.now()
        repayment.save()
        
        serializer = self.get_serializer(repayment)
        return Response(serializer.data)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for Notifications (read-only)
    """
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['user', 'is_read']
    ordering_fields = ['created_at']
    
    def get_queryset(self):
        """Filter notifications for current user"""
        return Notification.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        serializer = self.get_serializer(notification)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({"detail": "All notifications marked as read"})


class EntryFeePaymentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Entry Fee Payments
    """
    queryset = EntryFeePayment.objects.all()
    serializer_class = EntryFeePaymentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['kikoba_membership', 'is_fully_paid']
    
    def get_queryset(self):
        """Filter entry fee payments for user's memberships"""
        user = self.request.user
        return EntryFeePayment.objects.filter(kikoba_membership__user=user)


class ShareContributionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Share Contributions
    """
    queryset = ShareContribution.objects.all()
    serializer_class = ShareContributionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['kikoba_membership', 'is_fully_paid']
    
    def get_queryset(self):
        """Filter share contributions for user's memberships"""
        user = self.request.user
        return ShareContribution.objects.filter(kikoba_membership__user=user)


class EmergencyFundContributionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Emergency Fund Contributions
    """
    queryset = EmergencyFundContribution.objects.all()
    serializer_class = EmergencyFundContributionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['kikoba_membership']
    
    def get_queryset(self):
        """Filter emergency fund contributions for user's memberships"""
        user = self.request.user
        return EmergencyFundContribution.objects.filter(kikoba_membership__user=user)
