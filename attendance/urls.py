from django.urls import path
from .views import manage_attendance

urlpatterns = [
    path('manage/', manage_attendance, name='manage_attendance'),
]