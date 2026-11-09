from django.urls import path
from batches import views

app_name = 'batches'

urlpatterns = [
    path('', views.batch_list, name='batch_list'),
    path('create/', views.batch_create, name='batch_create'),
    path('<int:batch_id>/', views.batch_detail, name='batch_detail'),
    path('<int:batch_id>/assign-staff/', views.batch_assign_staff, name='batch_assign_staff'),
    path('<int:batch_id>/enroll-student/', views.enroll_student, name='enroll_student'),
    path('staff/', views.manage_staff, name='manage_staff'),
    path('staff/create/', views.create_staff, name='create_staff'),
]

