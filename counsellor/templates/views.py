"""
Counsellor: view students by risk, appointment requests, approve/complete, chat history.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import User
from student.models import ChatLog, Appointment, Assessment
from bson.objectid import ObjectId
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def _latest_assessment_for_user(user_id):
    """Return latest Assessment doc for user_id (MongoDB) or None."""
    try:
        return Assessment.objects.filter(user_id=user_id).order_by('-created_at').first()
    except Exception:
        try:
            return Assessment.objects.filter(user_id=user_id).order_by('-date').first()
        except Exception:
            return None


@login_required
def counsellor_dashboard(request):
    if getattr(request.user, 'role', None) != 'Counsellor':
        messages.warning(request, 'Access denied.')
        return redirect('accounts:login')

    students = list(User.objects.filter(role='Student').order_by('-risk_score', 'name'))
    # determine if any student has been flagged high-risk (is_flagged_high)
    flagged_exists = any(u.is_flagged_high for u in students)
    student_data = []
    for u in students:
        latest = _latest_assessment_for_user(u.id)
        student_data.append({
            'user': u,
            'latest_phq': getattr(latest, 'phq_score', None) or getattr(latest, 'total_score', None),
            'latest_gad': getattr(latest, 'gad_score', None),
        })

    high_risk = [s for s in student_data if s['user'].current_stress_level == 'High']
    medium_risk = [s for s in student_data if s['user'].current_stress_level == 'Medium']
    low_risk = [s for s in student_data if s['user'].current_stress_level == 'Low']

    appointments = list(Appointment.objects.filter(counsellor_id=request.user.id).order_by('-date'))

    return render(request, 'counsellor/counsellor_dashboard.html', {
        'high_risk_students': high_risk,
        'medium_risk_students': medium_risk,
        'low_risk_students': low_risk,
        'appointments': appointments,
        'flagged_exists': flagged_exists,
    })


@login_required
def appointment_update(request, appointment_id):
    if getattr(request.user, 'role', None) != 'Counsellor':
        return redirect('accounts:login')
    if request.method != 'POST':
        return redirect('counsellor:counsellor_dashboard')

    status = (request.POST.get('status') or '').strip()
    if status not in ('Approved', 'Completed'):
        messages.error(request, 'Invalid status.')
        return redirect('counsellor:counsellor_dashboard')

    try:
        app = Appointment.objects.get(id=ObjectId(appointment_id))
        # Security check: ensure counsellor can only update their own appointments
        if app.counsellor_id != request.user.id:
            messages.error(request, 'You can only update your own appointments.')
            logger.warning(f'Counsellor {request.user.id} tried to update appointment {appointment_id} belonging to counsellor {app.counsellor_id}')
            return redirect('counsellor:counsellor_dashboard')
    except (Appointment.DoesNotExist, Exception) as e:
        logger.error(f'Error fetching appointment: {str(e)}')
        messages.error(request, 'Appointment not found.')
        return redirect('counsellor:counsellor_dashboard')

    try:
        app.status = status
        app.save()
        messages.success(request, f'Appointment marked as {status}.')
    except Exception as e:
        logger.error(f'Error updating appointment: {str(e)}')
        messages.error(request, 'Failed to update appointment.')
    return redirect('counsellor:counsellor_dashboard')


@login_required
def student_chat_history(request, student_id):
    if getattr(request.user, 'role', None) != 'Counsellor':
        return redirect('accounts:login')
    try:
        student = User.objects.get(id=student_id, role='Student')
    except User.DoesNotExist:
        messages.error(request, 'Student not found.')
        return redirect('counsellor:counsellor_dashboard')
    logs = list(ChatLog.objects.filter(user_id=student_id).order_by('-timestamp'))
    return render(request, 'counsellor/chat_history.html', {
        'student': student,
        'chat_logs': logs,
    })


@login_required
def schedule_session_view(request, student_id):
    if getattr(request.user, 'role', None) != 'Counsellor':
        return redirect('accounts:login')
    try:
        student = User.objects.get(id=student_id, role='Student')
    except User.DoesNotExist:
        messages.error(request, 'Student not found.')
        return redirect('counsellor:counsellor_dashboard')
    if request.method == 'POST':
        date = (request.POST.get('date') or '').strip()
        if not date:
            messages.error(request, 'Please select a date.')
            return render(request, 'counsellor/schedule_session.html', {'student': student})
        
        # Validate date format and ensure future date
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            if date_obj.date() < datetime.now().date():
                messages.error(request, 'Please select a future date.')
                return render(request, 'counsellor/schedule_session.html', {'student': student})
        except ValueError:
            messages.error(request, 'Invalid date format.')
            return render(request, 'counsellor/schedule_session.html', {'student': student})
        
        try:
            Appointment(
                student_id=student_id,
                counsellor_id=request.user.id,
                date=date,
                status='Pending',
            ).save()
            messages.success(request, f'Session scheduled for {student.name}.')
            return redirect('counsellor:counsellor_dashboard')
        except Exception as e:
            logger.error(f'Error scheduling session: {str(e)}')
            messages.error(request, 'Failed to schedule session.')
    return render(request, 'counsellor/schedule_session.html', {'student': student})
