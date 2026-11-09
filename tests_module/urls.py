from django.urls import path
from tests_module import views

app_name = 'tests_module'

urlpatterns = [
    # Staff / Admin routes
    path('', views.test_list, name='test_list'),
    path('create/', views.create_test, name='create_test'),
    path('<int:test_id>/', views.test_detail, name='test_detail'),
    path('<int:test_id>/publish/', views.toggle_publish, name='toggle_publish'),

    # Student test taking & proctoring routes
    path('student/portal/', views.student_test_portal, name='student_portal'),
    path('<int:test_id>/take/', views.take_test, name='take_test'),
    path('attempt/<int:attempt_id>/tab-switch/', views.log_tab_switch, name='log_tab_switch'),
    path('attempt/<int:attempt_id>/submit/', views.submit_test, name='submit_test'),
    path('attempt/<int:attempt_id>/result/', views.test_result, name='test_result'),
]
