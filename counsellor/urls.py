from django.urls import path
from . import views

app_name = 'counsellor'

urlpatterns = [
    path('', views.counsellor_dashboard, name='counsellor_dashboard'),
    path('appointment/<str:appointment_id>/', views.appointment_update, name='appointment_update'),
    path('student/<int:student_id>/chat/', views.student_chat_history, name='student_chat_history'),
    path('student/<int:student_id>/message/', views.send_student_message, name='send_student_message'),
    path('student/<int:student_id>/session-note/', views.add_session_note, name='add_session_note'),
    path('student/<int:student_id>/care-task/', views.add_care_task, name='add_care_task'),
    path('student/<int:student_id>/schedule/', views.schedule_session_view, name='schedule_session'),
    path('student/<int:student_id>/risk-override/', views.risk_override, name='risk_override'),
    path('student/<int:student_id>/emergency-flag/', views.emergency_flag, name='emergency_flag'),
]
