
from django.urls import path
from .views import role_redirect

urlpatterns = [
    path('redirect/', role_redirect, name='role_redirect'),
]
