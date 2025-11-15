from django.urls import path
from .views import (
    LandingPageView, 
    AboutView, 
    ContactView, 
    FeaturesView, 
    DownloadView, 
    TrainingCenterView
)

app_name = 'landing'

urlpatterns = [
    path('', LandingPageView.as_view(), name='index'),
    path('about/', AboutView.as_view(), name='about'),
    path('contact/', ContactView.as_view(), name='contact'),
    path('features/', FeaturesView.as_view(), name='features'),
    path('download/', DownloadView.as_view(), name='download'),
    path('training-center/', TrainingCenterView.as_view(), name='training'),
]
