from django.urls import path
from . import views

app_name = 'counsellor'

urlpatterns = [
    path('', views.counsellor_dashboard, name='counsellor_dashboard'),
    path('appointment/<str:appointment_id>/', views.appointment_update, name='appointment_update'),
    path('student/<int:student_id>/chat/', views.student_chat_history, name='student_chat_history'),
    path('student/<int:student_id>/schedule/', views.schedule_session_view, name='schedule_session'),
]
