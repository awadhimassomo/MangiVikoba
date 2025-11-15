from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, permissions, status, filters, serializers # Added serializers
from rest_framework.exceptions import PermissionDenied # Added PermissionDenied
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Loan, Repayment, LoanApplication, LoanProduct # Corrected import
from .serializers import LoanSerializer, RepaymentSerializer, LoanApplicationSerializer, LoanProductSerializer # Ensure all serializers are imported
from groups.models import Kikoba, KikobaMembership # Added KikobaMembership import
from django.core.exceptions import PermissionDenied # Added import
from django.db.models import Q
from django.utils import timezone

class IsGroupAdminOrSelf(permissions.BasePermission):
    """
    Custom permission to only allow group admins or the user themselves (for applications/loans).
    """
    def has_object_permission(self, request, view, obj):
        # Determine the Kikoba instance and the relevant user (member/borrower)
        kikoba_instance = None
        relevant_user = None

        if isinstance(obj, Loan):
            if hasattr(obj, 'application') and obj.application:
                kikoba_instance = obj.application.kikoba
                relevant_user = obj.application.member
        elif isinstance(obj, LoanApplication):
            kikoba_instance = obj.kikoba
            relevant_user = obj.member
        elif isinstance(obj, Repayment):
            if hasattr(obj, 'loan') and obj.loan and hasattr(obj.loan, 'application') and obj.loan.application:
                kikoba_instance = obj.loan.application.kikoba
                relevant_user = obj.loan.application.member
        
        if not kikoba_instance or not relevant_user:
            return False # Cannot determine context

        # Allow read access if user is the relevant user or an admin of the Kikoba
        if request.method in permissions.SAFE_METHODS:
            is_kikoba_member_or_admin = KikobaMembership.objects.filter(
                kikoba=kikoba_instance,
                user=request.user,
                is_active=True # Optionally check for admin roles here if only admins can see other's loans
            ).exists()
            return relevant_user == request.user or is_kikoba_member_or_admin
        
        # Write permissions only for admins of the Kikoba
        return KikobaMembership.objects.filter(
            kikoba=kikoba_instance,
            user=request.user,
            role__in=['chairperson', 'treasurer', 'kikoba_admin'],
            is_active=True
        ).exists()

class LoanViewSet(viewsets.ModelViewSet):
    serializer_class = LoanSerializer
    permission_classes = [permissions.IsAuthenticated, IsGroupAdminOrSelf]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['application__member__name', 'application__kikoba__name', 'application__loan_product__name'] # Updated search fields
    ordering_fields = ['disbursement_date', 'total_repayable', 'status', 'application__application_date'] # Updated ordering fields
    ordering = ['-disbursement_date']
    
    def get_queryset(self):
        user = self.request.user
        queryset = Loan.objects.select_related(
            'application__member', 
            'application__kikoba', 
            'application__loan_product',
            'application__decision_by'
        ).all()

        if user.is_staff or user.is_superuser:
            return queryset
        
        admin_kikoba_ids = KikobaMembership.objects.filter(
            user=user,
            role__in=['chairperson', 'treasurer', 'kikoba_admin'],
            is_active=True
        ).values_list('kikoba_id', flat=True)
        
        return queryset.filter(
            Q(application__member=user) | Q(application__kikoba_id__in=list(admin_kikoba_ids))
        ).distinct()

    @action(detail=True, methods=['post'])
    def record_repayment(self, request, pk=None):
        loan = self.get_object()
        serializer = RepaymentSerializer(data=request.data, context={'request': request, 'loan': loan})
        if serializer.is_valid():
            serializer.save() # Loan is passed in context, serializer handles associating it
            if hasattr(loan, 'update_loan_status') and callable(loan.update_loan_status):
                 loan.update_loan_status() 
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def repayments(self, request, pk=None):
        loan = self.get_object()
        repayments = Repayment.objects.filter(loan=loan)
        serializer = RepaymentSerializer(repayments, many=True, context={'request': request})
        return Response(serializer.data)

class RepaymentViewSet(viewsets.ModelViewSet):
    serializer_class = RepaymentSerializer
    permission_classes = [permissions.IsAuthenticated, IsGroupAdminOrSelf] # Added IsGroupAdminOrSelf
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['loan__application__member__name', 'loan__application__kikoba__name', 'transaction_reference']
    ordering_fields = ['payment_date', 'amount_paid']
    ordering = ['-payment_date']

    def get_queryset(self):
        user = self.request.user
        queryset = Repayment.objects.select_related(
            'loan__application__member', 
            'loan__application__kikoba', 
            'verified_by'
        ).all()

        if user.is_staff or user.is_superuser:
            return queryset

        admin_kikoba_ids = KikobaMembership.objects.filter(
            user=user,
            role__in=['chairperson', 'treasurer', 'kikoba_admin'],
            is_active=True
        ).values_list('kikoba_id', flat=True)
        
        return queryset.filter(
            Q(loan__application__member=user) | Q(loan__application__kikoba_id__in=list(admin_kikoba_ids))
        ).distinct()

    def perform_create(self, serializer):
        loan_id = self.request.data.get('loan') # Assuming loan ID is passed directly
        if not loan_id:
            # If loan is part of the URL (e.g., nested router), get it from there
            loan_pk_from_url = self.kwargs.get('loan_pk') # Adjust if your URL structure is different
            if loan_pk_from_url:
                loan_id = loan_pk_from_url
            else:
                 raise serializers.ValidationError("Loan ID must be provided either in data or URL.")
        
        try:
            loan = Loan.objects.get(pk=loan_id)
            # Permission check: Is user allowed to record repayment for this loan?
            is_borrower = loan.application.member == self.request.user
            is_kikoba_admin = KikobaMembership.objects.filter(
                kikoba=loan.application.kikoba,
                user=self.request.user,
                role__in=['chairperson', 'treasurer', 'kikoba_admin'],
                is_active=True
            ).exists()

            if not (is_borrower or is_kikoba_admin or self.request.user.is_staff):
                raise PermissionDenied("You do not have permission to record a repayment for this loan.")
            
            # Pass validated_data and loan to serializer.save()
            # The serializer should handle associating the loan if it's not already done via context
            serializer.save(loan=loan) 
        except Loan.DoesNotExist:
            raise serializers.ValidationError(f"Loan with ID {loan_id} not found.")
        except Exception as e:
            raise serializers.ValidationError(str(e))

class LoanApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = LoanApplicationSerializer
    permission_classes = [permissions.IsAuthenticated, IsGroupAdminOrSelf]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['member__name', 'kikoba__name', 'loan_product__name', 'purpose']
    ordering_fields = ['application_date', 'requested_amount', 'status']
    ordering = ['-application_date']

    def get_queryset(self):
        user = self.request.user
        queryset = LoanApplication.objects.select_related(
            'member', 
            'kikoba', 
            'loan_product', 
            'decision_by'
        ).all()

        if user.is_staff or user.is_superuser:
            return queryset

        admin_kikoba_ids = KikobaMembership.objects.filter(
            user=user,
            role__in=['chairperson', 'treasurer', 'kikoba_admin'],
            is_active=True
        ).values_list('kikoba_id', flat=True)
        
        return queryset.filter(
            Q(member=user) | Q(kikoba_id__in=list(admin_kikoba_ids))
        ).distinct()

    def perform_create(self, serializer):
        # When a member creates a loan application, associate them and their kikoba if applicable
        # Kikoba might be selected from a list of their memberships
        kikoba_id = self.request.data.get('kikoba')
        if not kikoba_id:
            raise serializers.ValidationError("Kikoba ID must be provided for the application.")
        try:
            kikoba = Kikoba.objects.get(pk=kikoba_id)
            # Check if user is a member of this kikoba
            if not KikobaMembership.objects.filter(user=self.request.user, kikoba=kikoba, is_active=True).exists():
                raise PermissionDenied("You are not an active member of the selected Kikoba.")
            serializer.save(member=self.request.user, kikoba=kikoba)
        except Kikoba.DoesNotExist:
            raise serializers.ValidationError("Selected Kikoba not found.")

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        application = self.get_object() # This will use IsGroupAdminOrSelf for permission
        if application.status != 'pending':
            return Response({'detail': 'Application is not pending approval.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Permission to approve is already implicitly checked by IsGroupAdminOrSelf for write actions
        # and the fact that this is a POST request on a specific object.

        application.status = 'approved'
        application.decision_by = request.user
        application.decision_date = timezone.now()
        application.save()
        
        # Create Loan instance if it doesn't exist (idempotency)
        loan_instance, created = Loan.objects.get_or_create(
            application=application,
            defaults={
                'disbursed_amount': application.requested_amount, 
                'disbursement_date': timezone.now().date(), 
                'interest_rate_at_disbursement': application.loan_product.interest_rate if application.loan_product else 0,
                'original_due_date': timezone.now().date() + timezone.timedelta(days=application.loan_product.max_duration_days if application.loan_product else 30), 
                'current_due_date': timezone.now().date() + timezone.timedelta(days=application.loan_product.max_duration_days if application.loan_product else 30), 
                'total_repayable': application.requested_amount * (1 + ((application.loan_product.interest_rate if application.loan_product else 0) / 100)), 
                'status': 'pending_disbursement' 
            }
        )
        if not created and loan_instance.status not in ['pending_disbursement', 'active']:
            # If loan exists and is already processed beyond pending/active, perhaps don't re-approve easily
            pass # Or update status if needed
        elif created:
            pass # Loan was newly created

        return Response(LoanApplicationSerializer(application, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        application = self.get_object() # Uses IsGroupAdminOrSelf
        if application.status != 'pending':
            return Response({'detail': 'Application is not pending rejection.'}, status=status.HTTP_400_BAD_REQUEST)

        application.status = 'rejected'
        application.decision_by = request.user
        application.decision_date = timezone.now()
        application.remarks = request.data.get('remarks', application.remarks)
        application.save()
        return Response(LoanApplicationSerializer(application, context={'request': request}).data)

class LoanProductViewSet(viewsets.ModelViewSet):
    queryset = LoanProduct.objects.all()
    serializer_class = LoanProductSerializer
    permission_classes = [permissions.IsAuthenticated] # Basic permission, adjust as needed

    # Add any custom actions or overrides here
    # For example, only admins should be able to create/update/delete products
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            # Assuming you have a way to check if user is a global admin or kikoba admin
            # This is a placeholder, implement your actual admin check
            if not self.request.user.is_staff: # or some other admin check
                raise PermissionDenied("You do not have permission to manage loan products.")
        return super().get_permissions()
