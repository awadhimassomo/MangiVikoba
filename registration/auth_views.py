from django.contrib.auth.views import LoginView as BaseLoginView
from django.urls import reverse_lazy
from django.shortcuts import redirect
from .forms import PINAuthenticationForm

class CustomLoginView(BaseLoginView):
    """Custom login view that handles redirection based on user role."""
    form_class = PINAuthenticationForm
    
    def get_success_url(self):
        """
        Redirect users based on their role after successful login.
        Superusers go to the super admin dashboard, others to their respective dashboards.
        """
        # Check if there's a next parameter in the URL
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
            
        # Get the user role from session (set by the authentication backend)
        user_role = self.request.session.get('user_role', '')
        
        # Redirect based on user role
        if user_role == 'superuser' or self.request.user.is_superuser:
            return reverse_lazy('dashboard:super_admin:dashboard')
        elif user_role == 'admin':
            # For admins, redirect to their Kikoba admin dashboard
            admin_membership = self.request.user.kikoba_memberships.filter(
                role__in=['chairperson', 'kikoba_admin', 'treasurer', 'secretary'],
                is_active=True
            ).first()
            if admin_membership:
                return reverse_lazy('dashboard:kikoba_admin_dashboard', kwargs={'kikoba_id': admin_membership.kikoba.id})
        
        # Default fallback for members or if no specific role is determined
        return reverse_lazy('dashboard:home')
