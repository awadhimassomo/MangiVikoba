from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Q

from savings.models import Saving, Contribution
from groups.models import Kikoba, KikobaMembership
from registration.models import User

class KikobaMemberContributionsView(APIView):
    """
    API endpoint to get all contributions for a specific member in a specific Kikoba group.
    Requires kikoba_id and member_id as URL parameters.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, kikoba_id, member_id):
        # Get the Kikoba and member
        kikoba = get_object_or_404(Kikoba, id=kikoba_id)
        member = get_object_or_404(User, id=member_id)
        
        # Verify the member belongs to this Kikoba
        if not KikobaMembership.objects.filter(kikoba=kikoba, member=member).exists():
            return Response(
                {'status': 'error', 'message': 'Member not found in this Kikoba group'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get all savings for this member in this Kikoba
        savings = Saving.objects.filter(
            kikoba_membership__kikoba=kikoba,
            kikoba_membership__member=member
        )
        
        # Get all contributions for this member in this Kikoba
        contributions = Contribution.objects.filter(
            kikoba=kikoba,
            member=member
        )
        
        # Calculate totals
        total_savings = savings.aggregate(total=Sum('amount'))['total'] or 0
        total_contributions = contributions.aggregate(total=Sum('amount'))['total'] or 0
        
        # Apply date filters if provided
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            savings = savings.filter(created_at__gte=start_date)
            contributions = contributions.filter(created_at__gte=start_date)
            
        if end_date:
            savings = savings.filter(created_at__lte=end_date)
            contributions = contributions.filter(created_at__lte=end_date)
        
        response_data = {
            'status': 'success',
            'kikoba': {
                'id': kikoba.id,
                'name': kikoba.name,
                'registration_number': kikoba.registration_number
            },
            'member': {
                'id': member.id,
                'name': member.get_full_name(),
                'member_id': member.member_id,
                'phone': member.phone_number
            },
            'stats': {
                'total_savings': float(total_savings),
                'total_contributions': float(total_contributions),
                'total_balance': float(total_savings + total_contributions)
            },
            'savings': [
                {
                    'id': s.id,
                    'amount': float(s.amount),
                    'transaction_date': s.transaction_date,
                    'transaction_reference': s.transaction_reference,
                    'status': s.status,
                    'created_at': s.created_at
                } for s in savings
            ],
            'contributions': [
                {
                    'id': c.id,
                    'amount': float(c.amount),
                    'date_contributed': c.date_contributed,
                    'transaction_reference': c.transaction_reference,
                    'is_verified': c.is_verified,
                    'verified_by': c.verified_by.id if c.verified_by else None,
                    'verified_at': c.verified_at,
                    'created_at': c.created_at
                } for c in contributions
            ]
        }
        
        return Response(response_data)
