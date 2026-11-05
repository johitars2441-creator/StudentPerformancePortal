from django.urls import path
from .views import manage_marks

urlpatterns = [
    path('manage/', manage_marks, name='manage_marks'),
]