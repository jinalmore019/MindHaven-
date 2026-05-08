"""
Admin: total users, total high-risk students, total appointments, delete user (basic CRUD).
"""
import json
from collections import defaultdict
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg, Count
from datetime import datetime, timedelta
from accounts.models import User
from student.models import ChatLog, Assessment, Appointment


@login_required
def admin_dashboard(request):
    if getattr(request.user, 'role', None) != 'Admin':
        messages.warning(request, 'Access denied.')
        return redirect('accounts:login')

    # Stats for cards
    total_users = User.objects.count()
    total_students = User.objects.filter(role='Student').count()
    total_counsellors = User.objects.filter(role='Counsellor').count()
    total_admins = User.objects.filter(role='Admin').count()
    
    risk_filter = (request.GET.get('risk_filter') or 'high').strip().lower()
    if risk_filter not in {'all', 'high'}:
        risk_filter = 'high'

    # High risk users
    high_risk_users = User.objects.filter(current_stress_level='High').order_by('-date_joined')
    total_high_risk = high_risk_users.count()
    
    # Appointments
    total_appointments = Appointment.objects.count()
    recent_appointments = Appointment.objects.all().order_by('-id')[:5]
    
    # Stress level distribution
    stress_low = User.objects.filter(role='Student', current_stress_level='Low').count()
    stress_medium = User.objects.filter(role='Student', current_stress_level='Medium').count()
    stress_high = User.objects.filter(role='Student', current_stress_level='High').count()
    total_stress_count = max(stress_low + stress_medium + stress_high, 1)

    risk_percentage_low = round((stress_low / total_stress_count) * 100)
    risk_percentage_medium = round((stress_medium / total_stress_count) * 100)
    risk_percentage_high = round((stress_high / total_stress_count) * 100)

    # Trend from assessments (last 7 days): high-risk and total screening volumes
    today = datetime.now().date()
    trend_days = [today - timedelta(days=day_offset) for day_offset in range(6, -1, -1)]
    trend_labels = [day.strftime('%d %b') for day in trend_days]
    high_by_day = defaultdict(int)
    total_by_day = defaultdict(int)
    assessments = list(Assessment.objects.order_by('-created_at')[:500])
    for assessment in assessments:
        created_at = getattr(assessment, 'created_at', None) or getattr(assessment, 'date', None)
        if not created_at:
            continue
        created_day = created_at.date()
        if created_day not in trend_days:
            continue
        total_by_day[created_day] += 1
        level = (getattr(assessment, 'final_level', '') or getattr(assessment, 'stress_level', '') or '').strip()
        if level == 'High':
            high_by_day[created_day] += 1

    trend_high_counts = [high_by_day.get(day, 0) for day in trend_days]
    trend_total_counts = [total_by_day.get(day, 0) for day in trend_days]

    # Priority list for intervention
    student_qs = User.objects.filter(role='Student')
    if risk_filter == 'high':
        student_qs = student_qs.filter(current_stress_level='High')
    top_risky_students = student_qs.order_by('-risk_score', '-is_flagged_high', '-date_joined')[:8]
    
    # Recent users
    users = User.objects.all().order_by('-date_joined')
 
    context = {
        'total_users': total_users,
        'total_students': total_students,
        'total_counsellors': total_counsellors,
        'total_admins': total_admins,
        'total_high_risk': total_high_risk,
        'high_risk_users': high_risk_users[:5],
        'total_appointments': total_appointments,
        'recent_appointments': recent_appointments,
        'stress_low': stress_low,
        'stress_medium': stress_medium,
        'stress_high': stress_high,
        'risk_percentage_low': risk_percentage_low,
        'risk_percentage_medium': risk_percentage_medium,
        'risk_percentage_high': risk_percentage_high,
        'trend_labels_json': json.dumps(trend_labels),
        'trend_high_counts_json': json.dumps(trend_high_counts),
        'trend_total_counts_json': json.dumps(trend_total_counts),
        'top_risky_students': top_risky_students,
        'risk_filter': risk_filter,
        'users': users,
    }
    
    return render(request, 'admin_panel/admin_dashboard.html', context)


@login_required
def user_delete(request, user_id):
    if getattr(request.user, 'role', None) != 'Admin':
        return redirect('accounts:login')
    if request.method != 'POST':
        return redirect('admin_panel:admin_dashboard')

    target = User.objects.filter(id=user_id).first()
    if not target:
        messages.error(request, 'User not found.')
        return redirect('admin_panel:admin_dashboard')
    if target.id == request.user.id:
        messages.error(request, 'You cannot delete yourself.')
        return redirect('admin_panel:admin_dashboard')

    target.delete()
    messages.success(request, 'User deleted.')
    return redirect('admin_panel:admin_dashboard')


@login_required
def manage_users(request):
    """View all users with ability to create/delete."""
    if getattr(request.user, 'role', None) != 'Admin':
        messages.warning(request, 'Access denied.')
        return redirect('accounts:login')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        role = request.POST.get('role', '').strip()
        password = request.POST.get('password', '').strip()

        if not all([name, email, role, password]):
            messages.error(request, 'All fields are required.')
        elif role not in ['Student', 'Counsellor', 'Admin']:
            messages.error(request, 'Invalid role selected.')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'A user with this email already exists.')
        elif len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters.')
        else:
            User.objects.create_user(email=email, name=name, role=role, password=password)
            messages.success(request, f'User "{name}" created successfully.')
        return redirect('admin_panel:manage_users')

    users = User.objects.all().order_by('-date_joined')
    return render(request, 'admin_panel/manage_users.html', {
        'users': users,
        'user_count': users.count(),
    })


@login_required
def edit_user(request, user_id):
    """View user information only. Admin cannot edit user details for security."""
    if getattr(request.user, 'role', None) != 'Admin':
        messages.warning(request, 'Access denied.')
        return redirect('accounts:login')
    
    user = User.objects.filter(id=user_id).first()
    if not user:
        messages.error(request, 'User not found.')
        return redirect('admin_panel:manage_users')
    
    # Admin can only VIEW user information, not edit
    if request.method == 'POST':
        messages.warning(request, 'User information cannot be modified from this page for security reasons.')
        return redirect('admin_panel:manage_users')
    
    return render(request, 'admin_panel/edit_user.html', {
        'user': user,
        'user_last_assessment': Assessment.objects.filter(user_id=user.id).order_by('-created_at').first(),
    })


@login_required
def delete_user(request, user_id):
    """Delete user safely."""
    if getattr(request.user, 'role', None) != 'Admin':
        messages.warning(request, 'Access denied.')
        return redirect('accounts:login')
    
    if request.method != 'POST':
        return redirect('admin_panel:manage_users')
    
    user = User.objects.filter(id=user_id).first()
    if not user:
        messages.error(request, 'User not found.')
        return redirect('admin_panel:manage_users')
    
    if user.id == request.user.id:
        messages.error(request, 'You cannot delete yourself.')
        return redirect('admin_panel:manage_users')
    
    user_name = user.name
    user.delete()
    messages.success(request, f'User "{user_name}" deleted successfully.')
    return redirect('admin_panel:manage_users')



@login_required
def reports_view(request):
    """Generate comprehensive reports for admin."""
    if getattr(request.user, 'role', None) != 'Admin':
        messages.warning(request, 'Access denied.')
        return redirect('accounts:login')
    
    # Mental Health Reports
    # PHQ-9 and GAD-7 averages (MongoEngine)
    assessments = list(Assessment.objects.all())
    
    if assessments:
        total_phq = sum(a.phq_score for a in assessments if a.phq_score)
        total_gad = sum(a.gad_score for a in assessments if a.gad_score)
        count_phq = sum(1 for a in assessments if a.phq_score)
        count_gad = sum(1 for a in assessments if a.gad_score)
        
        phq_avg = round(total_phq / count_phq, 2) if count_phq > 0 else 0
        gad_avg = round(total_gad / count_gad, 2) if count_gad > 0 else 0
    else:
        phq_avg = 0
        gad_avg = 0
    
    # Stress distribution
    stress_low = User.objects.filter(role='Student', current_stress_level='Low').count()
    stress_medium = User.objects.filter(role='Student', current_stress_level='Medium').count()
    stress_high = User.objects.filter(role='Student', current_stress_level='High').count()
    
    # High-risk trends
    now = datetime.now()
    last_7_days = now - timedelta(days=7)
    last_30_days = now - timedelta(days=30)
    
    high_risk_7_days = User.objects.filter(
        role='Student',
        current_stress_level='High',
        date_joined__gte=last_7_days
    ).count()
    
    high_risk_30_days = User.objects.filter(
        role='Student',
        current_stress_level='High',
        date_joined__gte=last_30_days
    ).count()
    
    # Appointment Reports
    total_sessions = Appointment.objects.count()
    completed_sessions = Appointment.objects.filter(status='Completed').count()
    pending_sessions = Appointment.objects.filter(status='Pending').count()
    
    # Counsellor-wise sessions
    counsellors = User.objects.filter(role='Counsellor')
    counsellor_stats = []
    for counsellor in counsellors:
        session_count = Appointment.objects.filter(counsellor_id=counsellor.id).count()
        counsellor_stats.append({
            'name': counsellor.name,
            'sessions': session_count
        })
    
    context = {
        'phq_avg': round(phq_avg, 2),
        'gad_avg': round(gad_avg, 2),
        'stress_low': stress_low,
        'stress_medium': stress_medium,
        'stress_high': stress_high,
        'high_risk_7_days': high_risk_7_days,
        'high_risk_30_days': high_risk_30_days,
        'total_sessions': total_sessions,
        'completed_sessions': completed_sessions,
        'pending_sessions': pending_sessions,
        'counsellor_stats': counsellor_stats,
    }
    
    return render(request, 'admin_panel/reports.html', context)


@login_required
def export_csv(request):
    """Export user data as CSV."""
    if getattr(request.user, 'role', None) != 'Admin':
        messages.warning(request, 'Access denied.')
        return redirect('accounts:login')
    
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="wellness_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Name', 'Email', 'Role', 'Stress Level', 'Risk Score'])
    
    users = User.objects.all()
    for user in users:
        writer.writerow([
            user.name,
            user.email,
            user.role,
            user.current_stress_level or 'Low',
            user.risk_score or 0
        ])
    
    return response


@login_required
def export_pdf(request):
    """Export report as PDF."""
    if getattr(request.user, 'role', None) != 'Admin':
        messages.warning(request, 'Access denied.')
        return redirect('accounts:login')
    
    from django.http import HttpResponse
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import inch
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="wellness_report.pdf"'
    
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter
    
    # Title
    p.setFont("Helvetica-Bold", 20)
    p.drawString(1*inch, height - 1*inch, "Wellness Connect - Report")
    
    # Summary Stats
    p.setFont("Helvetica-Bold", 14)
    p.drawString(1*inch, height - 1.5*inch, "Summary Statistics")
    
    p.setFont("Helvetica", 12)
    y = height - 1.8*inch
    
    total_users = User.objects.count()
    total_students = User.objects.filter(role='Student').count()
    high_risk = User.objects.filter(current_stress_level='High').count()
    
    p.drawString(1*inch, y, f"Total Users: {total_users}")
    y -= 0.3*inch
    p.drawString(1*inch, y, f"Total Students: {total_students}")
    y -= 0.3*inch
    p.drawString(1*inch, y, f"High Risk Users: {high_risk}")
    y -= 0.5*inch
    
    # Stress Distribution
    p.setFont("Helvetica-Bold", 14)
    p.drawString(1*inch, y, "Stress Distribution")
    y -= 0.3*inch
    
    p.setFont("Helvetica", 12)
    stress_low = User.objects.filter(role='Student', current_stress_level='Low').count()
    stress_medium = User.objects.filter(role='Student', current_stress_level='Medium').count()
    stress_high = User.objects.filter(role='Student', current_stress_level='High').count()
    
    p.drawString(1*inch, y, f"Low: {stress_low}")
    y -= 0.3*inch
    p.drawString(1*inch, y, f"Medium: {stress_medium}")
    y -= 0.3*inch
    p.drawString(1*inch, y, f"High: {stress_high}")
    y -= 0.5*inch
    
    # Appointments
    p.setFont("Helvetica-Bold", 14)
    p.drawString(1*inch, y, "Appointment Summary")
    y -= 0.3*inch
    
    p.setFont("Helvetica", 12)
    total_appointments = Appointment.objects.count()
    completed = Appointment.objects.filter(status='Completed').count()
    pending = Appointment.objects.filter(status='Pending').count()
    
    p.drawString(1*inch, y, f"Total Sessions: {total_appointments}")
    y -= 0.3*inch
    p.drawString(1*inch, y, f"Completed: {completed}")
    y -= 0.3*inch
    p.drawString(1*inch, y, f"Pending: {pending}")
    
    # Footer
    p.setFont("Helvetica", 10)
    p.drawString(1*inch, 0.5*inch, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    p.showPage()
    p.save()
    
    return response



@login_required
def erp_integration(request):
    """ERP/LMS Integration demo page."""
    if getattr(request.user, 'role', None) != 'Admin':
        messages.warning(request, 'Access denied.')
        return redirect('accounts:login')
    
    connection_status = request.session.get('erp_connected', False)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # Simulate connection
        if action == 'connect':
            request.session['erp_connected'] = True
            messages.success(request, 'Successfully connected to ERP/LMS system!')
            return redirect('admin_panel:erp_integration')
        
        # Disconnect
        elif action == 'disconnect':
            request.session['erp_connected'] = False
            messages.info(request, 'Disconnected from ERP/LMS system.')
            return redirect('admin_panel:erp_integration')
        
        # CSV Upload
        elif action == 'upload_csv':
            if not connection_status:
                messages.error(request, 'Please connect to ERP/LMS first.')
                return redirect('admin_panel:erp_integration')
            
            csv_file = request.FILES.get('csv_file')
            if not csv_file:
                messages.error(request, 'Please select a CSV file.')
                return redirect('admin_panel:erp_integration')
            
            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'Please upload a valid CSV file.')
                return redirect('admin_panel:erp_integration')
            
            try:
                import csv
                import io
                
                # Read CSV
                decoded_file = csv_file.read().decode('utf-8')
                io_string = io.StringIO(decoded_file)
                reader = csv.DictReader(io_string)
                
                created_count = 0
                skipped_count = 0
                
                for row in reader:
                    name = row.get('name', '').strip()
                    email = row.get('email', '').strip()
                    role = row.get('role', '').strip()
                    
                    # Validate
                    if not name or not email or not role:
                        skipped_count += 1
                        continue
                    
                    if role not in ['Student', 'Counsellor', 'Admin']:
                        skipped_count += 1
                        continue
                    
                    # Check if user exists
                    if User.objects.filter(email=email).exists():
                        skipped_count += 1
                        continue
                    
                    # Create user with default password
                    User.objects.create_user(
                        email=email,
                        name=name,
                        role=role,
                        password='Welcome@123'  # Default password
                    )
                    created_count += 1
                
                messages.success(request, f'Successfully created {created_count} users. Skipped {skipped_count} entries.')
                
            except Exception as e:
                messages.error(request, f'Error processing CSV: {str(e)}')
            
            return redirect('admin_panel:erp_integration')
    
    return render(request, 'admin_panel/erp_integration.html', {
        'connection_status': connection_status
    })
