"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from accounts.views import role_redirect

urlpatterns = [
    path('', role_redirect, name='home'),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('analytics/', include('analytics.urls')),
    path('accounts/', include('accounts.urls')),
    path('batches/', include('batches.urls')),
    path('tests/', include('tests_module.urls')),
    path('mock-interviews/', include('mock_interviews.urls')),
    path('student/', include('students.urls')),
    path('subjects/', include('subjects.urls')),
    path('marks/', include('marks.urls')),
    path('attendance/', include('attendance.urls')),
]
