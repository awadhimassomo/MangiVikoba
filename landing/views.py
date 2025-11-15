from django.shortcuts import render
from django.views.generic import TemplateView
from learning.models import LearningCategory, LearningContent

class LandingPageView(TemplateView):
    template_name = "landing/index.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get featured learning content for the landing page
        context['featured_categories'] = LearningCategory.objects.filter(is_active=True)[:3]
        context['featured_content'] = LearningContent.objects.filter(is_active=True, is_featured=True)[:4]
        return context

class AboutView(TemplateView):
    template_name = "landing/about.html"

class ContactView(TemplateView):
    template_name = "landing/contact.html"

class FeaturesView(TemplateView):
    template_name = "landing/features.html"

class DownloadView(TemplateView):
    template_name = "landing/download.html"

class TrainingCenterView(TemplateView):
    template_name = "landing/training.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = LearningCategory.objects.filter(is_active=True)
        context['content'] = LearningContent.objects.filter(is_active=True)
        return context
