from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import RegisterView, UserProfileView, UpdateUserProfileView, unified_registration
from . import views

app_name = 'registration'  # Define the application namespace

urlpatterns = [
    path('register/', views.unified_registration, name='unified_register'),
    # path('register/kikoba/', views.register_kikoba, name='register_kikoba'),
    # path('register/member/', views.register_member, name='register_member'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('profile/update/', UpdateUserProfileView.as_view(), name='update_profile'),
]
