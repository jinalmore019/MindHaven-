from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from datetime import datetime

from accounts.models import User
from student.models import (
    Appointment,
    Assessment,
    CareTask,
    ChatLog,
    CounsellorMessage,
    CounsellorSessionNote,
    DailyPost,
    StudentReply,
)


COUNSELLOR_PROFILES = {
    "counsellor.riya@wellify.demo": {
        "designation": "Clinical Psychologist",
        "experience": "7 years",
        "specializations": ["Anxiety", "Student Burnout", "Self-esteem"],
        "languages": ["English", "Hindi", "Gujarati"],
        "bio": "Focuses on student stress, panic regulation, and recovery planning.",
    },
    "counsellor.arjun@wellify.demo": {
        "designation": "Counselling Psychologist",
        "experience": "5 years",
        "specializations": ["Academic Stress", "Sleep Issues", "Mood Support"],
        "languages": ["English", "Hindi"],
        "bio": "Works with performance pressure, emotional fatigue, and practical coping plans.",
    },
}


def _build_counsellor_profile(user):
    default_profile = {
        "designation": "Student Wellness Counsellor",
        "experience": "3+ years",
        "specializations": ["Emotional Support", "Academic Stress", "Crisis Triage"],
        "languages": ["English", "Hindi"],
        "bio": "Provides supportive guidance, risk triage, and structured follow-up for students.",
    }
    profile = COUNSELLOR_PROFILES.get(user.email, default_profile).copy()
    profile["name"] = user.name
    profile["email"] = user.email
    return profile


def _latest_assessment_for_user(user_id):
    try:
        return Assessment.objects.filter(user_id=user_id).order_by("-created_at").first()
    except Exception:
        try:
            return Assessment.objects.filter(user_id=user_id).order_by("-date").first()
        except Exception:
            return None


@login_required
def counsellor_dashboard(request):
    if getattr(request.user, "role", None) != "Counsellor":
        messages.warning(request, "Access denied.")
        return redirect("accounts:login")

    students = list(User.objects.filter(role="Student").order_by("-risk_score", "name"))
    student_data = []

    for user in students:
        latest = _latest_assessment_for_user(user.id)
        student_data.append(
            {
                "user": user,
                "latest_phq": getattr(latest, "phq_score", None) or getattr(latest, "total_score", None),
                "latest_gad": getattr(latest, "gad_score", None),
            }
        )

    high_risk = [s for s in student_data if s["user"].current_stress_level == "High"]
    medium_risk = [s for s in student_data if s["user"].current_stress_level == "Medium"]
    low_risk = [s for s in student_data if s["user"].current_stress_level == "Low"]

    appointments = list(Appointment.objects.filter(counsellor_id=request.user.id).order_by("-date"))
    student_lookup = {student.id: student for student in students}
    appointment_cards = []
    for appointment in appointments:
        appointment_cards.append(
            {
                "id": appointment.id,
                "date": appointment.date,
                "status": appointment.status,
                "student": student_lookup.get(appointment.student_id),
            }
        )

    pending_student_ids = {
        item.student_id for item in appointments if item.status in ("Pending", "Approved")
    }
    priority_cases = []
    for entry in high_risk:
        student = entry["user"]
        recent_chat = ChatLog.objects.filter(user_id=student.id).order_by("-timestamp").first()
        priority_cases.append(
            {
                "user": student,
                "latest_phq": entry["latest_phq"],
                "latest_gad": entry["latest_gad"],
                "has_active_session": student.id in pending_student_ids,
                "last_chat_at": getattr(recent_chat, "timestamp", None),
            }
        )

    # Highest urgency first: high risk students without active session.
    priority_cases.sort(
        key=lambda item: (
            item["has_active_session"],
            -(item["user"].risk_score or 0),
            -(item["latest_phq"] or 0),
            -(item["latest_gad"] or 0),
        )
    )

    priority_posts_raw = list(DailyPost.objects.filter(stress_level__in=["High", "Medium"]).order_by("-created_at")[:8])
    priority_posts = []
    for post in priority_posts_raw:
        student = student_lookup.get(post.user_id)
        priority_posts.append(
            {
                "author_name": student.name if student else f"Student #{post.user_id}",
                "created_at": post.created_at,
                "language": post.language,
                "stress_level": post.stress_level,
                "content": post.content,
            }
        )

    context = {
        "high_risk_students": high_risk,
        "medium_risk_students": medium_risk,
        "low_risk_students": low_risk,
        "priority_cases": priority_cases[:6],
        "appointments": appointment_cards,
        "total_students": len(student_data),
        "high_count": len(high_risk),
        "medium_count": len(medium_risk),
        "low_count": len(low_risk),
        "pending_count": sum(1 for app in appointments if app.status == "Pending"),
        "priority_posts": priority_posts,
        "counsellor_profile": _build_counsellor_profile(request.user),
        "active_sessions_count": sum(1 for app in appointments if app.status == "Approved"),
        "completed_sessions_count": sum(1 for app in appointments if app.status == "Completed"),
    }
    return render(request, "counsellor/counsellor_dashboard.html", context)


@login_required
def appointment_update(request, appointment_id):
    if getattr(request.user, "role", None) != "Counsellor":
        return redirect("accounts:login")
    if request.method != "POST":
        return redirect("counsellor:counsellor_dashboard")

    status = (request.POST.get("status") or "").strip()
    if status not in ("Approved", "Completed"):
        messages.error(request, "Invalid status.")
        return redirect("counsellor:counsellor_dashboard")

    try:
        from bson.objectid import ObjectId

        appointment = Appointment.objects.get(id=ObjectId(appointment_id), counsellor_id=request.user.id)
    except (Appointment.DoesNotExist, Exception):
        messages.error(request, "Appointment not found.")
        return redirect("counsellor:counsellor_dashboard")

    appointment.status = status
    appointment.save()
    messages.success(request, f"Appointment marked as {status}.")
    return redirect("counsellor:counsellor_dashboard")


@login_required
def student_chat_history(request, student_id):
    if getattr(request.user, "role", None) != "Counsellor":
        return redirect("accounts:login")

    try:
        student = User.objects.get(id=student_id, role="Student")
    except User.DoesNotExist:
        messages.error(request, "Student not found.")
        return redirect("counsellor:counsellor_dashboard")

    logs = list(ChatLog.objects.filter(user_id=student_id).order_by("-timestamp"))
    counsellor_messages = list(
        CounsellorMessage.objects.filter(student_id=student_id).order_by("-created_at")[:20]
    )
    counsellor_lookup = {
        user.id: user
        for user in User.objects.filter(id__in=[item.counsellor_id for item in counsellor_messages])
    }
    for item in counsellor_messages:
        item.counsellor_name = counsellor_lookup.get(item.counsellor_id).name if counsellor_lookup.get(item.counsellor_id) else "Counsellor"
    session_notes = list(CounsellorSessionNote.objects.filter(student_id=student_id).order_by("-created_at")[:8])
    care_tasks = list(CareTask.objects.filter(student_id=student_id).order_by("-created_at")[:10])
    latest = _latest_assessment_for_user(student_id)
    # Build merged chat thread: counsellor messages + student replies sorted by time
    c_msgs = list(CounsellorMessage.objects.filter(student_id=student_id).order_by("-created_at")[:30])
    s_replies = list(StudentReply.objects.filter(student_id=student_id).order_by("-created_at")[:30])
    counsellor_lookup = {
        user.id: user
        for user in User.objects.filter(id__in=[item.counsellor_id for item in c_msgs])
    }
    chat_thread = []
    for m in c_msgs:
        chat_thread.append({'sender': 'counsellor', 'name': counsellor_lookup.get(m.counsellor_id).name if counsellor_lookup.get(m.counsellor_id) else 'Counsellor', 'message': m.message, 'created_at': m.created_at})
    for r in s_replies:
        chat_thread.append({'sender': 'student', 'name': student.name, 'message': r.message, 'created_at': r.created_at})
    chat_thread.sort(key=lambda x: x['created_at'])
    return render(
        request,
        "counsellor/chat_history.html",
        {
            "student": student,
            "chat_logs": logs,
            "chat_thread": chat_thread,
            "session_notes": session_notes,
            "care_tasks": care_tasks,
            "latest_assessment": latest,
        },
    )


@login_required
@require_POST
def send_student_message(request, student_id):
    if getattr(request.user, "role", None) != "Counsellor":
        return redirect("accounts:login")
    try:
        student = User.objects.get(id=student_id, role="Student")
    except User.DoesNotExist:
        messages.error(request, "Student not found.")
        return redirect("counsellor:counsellor_dashboard")

    body = (request.POST.get("message") or "").strip()
    if not body:
        messages.error(request, "Message cannot be empty.")
        return redirect("counsellor:student_chat_history", student_id=student.id)
    CounsellorMessage(
        student_id=student.id,
        counsellor_id=request.user.id,
        message=body,
    ).save()
    messages.success(request, "Message sent to student.")
    return redirect("counsellor:student_chat_history", student_id=student.id)


@login_required
def add_session_note(request, student_id):
    if getattr(request.user, "role", None) != "Counsellor":
        return redirect("accounts:login")
    try:
        student = User.objects.get(id=student_id, role="Student")
    except User.DoesNotExist:
        messages.error(request, "Student not found.")
        return redirect("counsellor:counsellor_dashboard")

    if request.method != "POST":
        return redirect("counsellor:student_chat_history", student_id=student_id)

    summary = (request.POST.get("summary") or "").strip()
    action_plan = (request.POST.get("action_plan") or "").strip()
    follow_up = (request.POST.get("next_follow_up_date") or "").strip()

    if not summary:
        messages.error(request, "Session summary is required.")
        return redirect("counsellor:student_chat_history", student_id=student_id)

    try:
        CounsellorSessionNote(
            student_id=student.id,
            counsellor_id=request.user.id,
            summary=summary,
            action_plan=action_plan,
            next_follow_up_date=follow_up,
        ).save()
        messages.success(request, "Session note saved successfully!")
    except Exception as e:
        messages.error(request, f"Error saving note: {e}")
    return redirect(f"/counsellor/student/{student_id}/chat/#session-notes")


@login_required
def add_care_task(request, student_id):
    if getattr(request.user, "role", None) != "Counsellor":
        return redirect("accounts:login")
    try:
        student = User.objects.get(id=student_id, role="Student")
    except User.DoesNotExist:
        messages.error(request, "Student not found.")
        return redirect("counsellor:counsellor_dashboard")

    if request.method != "POST":
        return redirect("counsellor:student_chat_history", student_id=student_id)

    title = (request.POST.get("title") or "").strip()
    details = (request.POST.get("details") or "").strip()
    due_date = (request.POST.get("due_date") or "").strip()

    if not title:
        messages.error(request, "Task title is required.")
        return redirect(f"/counsellor/student/{student_id}/chat/#session-notes")

    try:
        CareTask(
            student_id=student.id,
            counsellor_id=request.user.id,
            title=title,
            details=details,
            due_date=due_date,
            status="Pending",
        ).save()
        messages.success(request, "Care task assigned successfully!")
    except Exception as e:
        messages.error(request, f"Error saving task: {e}")
    return redirect(f"/counsellor/student/{student_id}/chat/#session-notes")


@login_required
@require_POST
def risk_override(request, student_id):
    if getattr(request.user, 'role', None) != 'Counsellor':
        return redirect('accounts:login')
    try:
        student = User.objects.get(id=student_id, role='Student')
    except User.DoesNotExist:
        messages.error(request, 'Student not found.')
        return redirect('counsellor:counsellor_dashboard')
    new_level = (request.POST.get('risk_level') or '').strip()
    if new_level not in ('Low', 'Medium', 'High'):
        messages.error(request, 'Invalid risk level.')
        return redirect('counsellor:student_chat_history', student_id=student.id)
    student.current_stress_level = new_level
    student.is_flagged_high = (new_level == 'High')
    student.save()
    messages.success(request, f'Risk level updated to {new_level} for {student.name}.')
    return redirect('counsellor:student_chat_history', student_id=student.id)


@login_required
@require_POST
def emergency_flag(request, student_id):
    if getattr(request.user, 'role', None) != 'Counsellor':
        return redirect('accounts:login')
    try:
        student = User.objects.get(id=student_id, role='Student')
    except User.DoesNotExist:
        messages.error(request, 'Student not found.')
        return redirect('counsellor:counsellor_dashboard')
    student.current_stress_level = 'High'
    student.is_flagged_high = True
    student.save()
    # Auto-create priority appointment
    existing = Appointment.objects.filter(student_id=student.id, status__in=('Pending', 'Approved')).first()
    if not existing:
        Appointment(student_id=student.id, counsellor_id=request.user.id, date=datetime.now().strftime('%Y-%m-%d'), status='Pending').save()
    messages.warning(request, f'🚨 Emergency flag set for {student.name}. Priority session created.')
    return redirect('counsellor:student_chat_history', student_id=student.id)


@login_required
def schedule_session_view(request, student_id):
    if getattr(request.user, "role", None) != "Counsellor":
        return redirect("accounts:login")

    try:
        student = User.objects.get(id=student_id, role="Student")
    except User.DoesNotExist:
        messages.error(request, "Student not found.")
        return redirect("counsellor:counsellor_dashboard")

    if request.method == "POST":
        date = (request.POST.get("date") or "").strip()
        if date:
            Appointment(
                student_id=student_id,
                counsellor_id=request.user.id,
                date=date,
                status="Pending",
            ).save()
            messages.success(request, f"Session scheduled for {student.name}.")
            return redirect("counsellor:counsellor_dashboard")
        messages.error(request, "Please select a date.")

    return render(request, "counsellor/schedule_session.html", {"student": student})
