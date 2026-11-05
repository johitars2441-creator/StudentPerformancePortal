from django.urls import path
from .views import manage_subjects

urlpatterns = [
    path('manage/', manage_subjects, name='manage_subjects'),
]