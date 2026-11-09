from django.urls import path
from mock_interviews import views

app_name = 'mock_interviews'

urlpatterns = [
    path('', views.interview_list, name='interview_list'),
    path('schedule/', views.schedule_interview, name='schedule_interview'),
    path('<int:interview_id>/evaluate/', views.evaluate_interview, name='evaluate_interview'),
    path('student/', views.student_mock_interviews, name='student_interviews'),
]
