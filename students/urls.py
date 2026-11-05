from django.urls import path
from .views import student_dashboard, manage_students

urlpatterns = [
    path("dashboard/", student_dashboard, name="student_dashboard"),
    path("manage/", manage_students, name="manage_students"),
]