from django.urls import path
from . import views

urlpatterns = [
    path('overview/', views.overview, name='analytics-overview'),
    path('results/',views.results,name='analytics-results'),
    path('dashboard/', views.dashboard, name='analytics-dashboard'),
    path('attendance-analytics/',views.attendance_analytics,name='attendance-analytics'),
    path('subject-performance/',views.subject_performance,name='subject-performance'),
    path('student-report/',views.student_analytics_report,name='student_analytics_report'),

]