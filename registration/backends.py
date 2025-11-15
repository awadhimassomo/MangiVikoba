from django.contrib.auth import get_user_model, login
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from django.conf import settings

UserModel = get_user_model()

class FlexibleLoginBackend(ModelBackend):
    def get_user_role(self, user):
        """Determine the user's role for redirection purposes."""
        if user.is_superuser:
            return 'superuser'
        if user.role in ['admin', 'kikoba_admin', 'chairperson', 'treasurer', 'secretary']:
            return 'admin'
        return 'member'

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)

        # Try to find user by user_identifier first (for admins)
        try:
            # Attempt to find user by user_identifier
            user = UserModel.objects.get(user_identifier=username)
            if user.check_password(password) and self.user_can_authenticate(user):
                if user.role in ['admin', 'kikoba_admin']:  # Ensure only admins can log in via user_identifier
                    # Store user role in session for post-login redirection
                    if hasattr(request, 'session'):
                        request.session['user_role'] = self.get_user_role(user)
                    return user
        except UserModel.DoesNotExist:
            # Fall through to try by phone_number
            pass
        except UserModel.MultipleObjectsReturned:
            return None


        # Fallback to default UserModel.USERNAME_FIELD (phone_number)
        try:
            user = UserModel.objects.get(phone_number=username)
            if user.check_password(password) and self.user_can_authenticate(user):
                # Store user role in session for post-login redirection
                if hasattr(request, 'session'):
                    request.session['user_role'] = self.get_user_role(user)
                return user
        except UserModel.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a non-existing user (#20760).
            UserModel().set_password(password)
        except UserModel.MultipleObjectsReturned:
            # This shouldn't happen if phone_number is unique.
            return None
            
        return None # Explicitly return None if no user is found or password doesn't match

    def get_user(self, user_id):
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None
