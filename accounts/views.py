from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils import translation
from .forms import RegisterForm


def login_view(request):
    """Login view with role-based authentication and redirect."""
    if request.user.is_authenticated:
        return redirect('accounts:role_redirect')
    
    if request.method == "POST":
        email = request.POST.get("username")  # Form field name is 'username'
        password = request.POST.get("password")
        selected_role = request.POST.get("role")

        if email and password and selected_role:
            user = authenticate(request, username=email, password=password)
            
            if user is not None:
                # Check if user's role matches selected role
                if user.role == selected_role:
                    login(request, user)
                    messages.success(request, f'Welcome back, {user.name}!')
                    
                    # Role-based redirect
                    if user.role == "Student":
                        return redirect("student:student_dashboard")
                    elif user.role == "Counsellor":
                        return redirect("counsellor:counsellor_dashboard")
                    elif user.role == "Admin":
                        return redirect("admin_panel:admin_dashboard")
                else:
                    messages.error(request, f'Selected role is incorrect. Your account is registered as {user.role}.')
            else:
                messages.error(request, 'Invalid email or password.')
        else:
            messages.error(request, 'Please fill in all fields.')

    return render(request, "accounts/login.html")


def register_view(request):
    """Register view with role-based redirect after registration."""
    if request.user.is_authenticated:
        return redirect('accounts:role_redirect')
    
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Account created successfully! Welcome, {user.name}!')
            
            # Role-based redirect
            if user.role == "Student":
                return redirect("student:student_dashboard")
            elif user.role == "Counsellor":
                return redirect("counsellor:counsellor_dashboard")
            elif user.role == "Admin":
                return redirect("admin_panel:admin_dashboard")
        else:
            messages.error(request, 'Please fix the errors below.')
            for field_name, field_errors in form.errors.items():
                label = form.fields.get(field_name).label if field_name in form.fields else "Form"
                for err in field_errors:
                    messages.error(request, f"{label}: {err}")
    else:
        form = RegisterForm()
    
    return render(request, "accounts/register.html", {'form': form})


@login_required
def logout_view(request):
    """Logout view."""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('accounts:login')


@login_required
def role_redirect_view(request):
    """Redirect user to their role-specific dashboard."""
    user = request.user
    if user.role == "Student":
        return redirect("student:student_dashboard")
    elif user.role == "Counsellor":
        return redirect("counsellor:counsellor_dashboard")
    elif user.role == "Admin":
        return redirect("admin_panel:admin_dashboard")
    else:
        messages.warning(request, 'Invalid role. Please contact administrator.')
        return redirect('accounts:login')


@login_required
def profile_view(request):
    """User profile page - users can update their own information."""
    user = request.user
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        current_password = request.POST.get('current_password', '').strip()
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        
        # Validate name
        if not name:
            messages.error(request, 'Name cannot be empty.')
            return render(request, 'accounts/profile.html', {'user': user})
        
        # Validate email
        if not email:
            messages.error(request, 'Email cannot be empty.')
            return render(request, 'accounts/profile.html', {'user': user})
        
        # Check if email is already taken by another user
        from .models import User
        if User.objects.filter(email=email).exclude(id=user.id).exists():
            messages.error(request, 'Email is already taken by another user.')
            return render(request, 'accounts/profile.html', {'user': user})
        
        # Update name and email
        user.name = name
        user.email = email
        
        # Password change logic
        if new_password:
            # Verify current password
            if not current_password:
                messages.error(request, 'Please enter your current password to change it.')
                return render(request, 'accounts/profile.html', {'user': user})
            
            if not user.check_password(current_password):
                messages.error(request, 'Current password is incorrect.')
                return render(request, 'accounts/profile.html', {'user': user})
            
            # Validate new password
            if new_password != confirm_password:
                messages.error(request, 'New passwords do not match.')
                return render(request, 'accounts/profile.html', {'user': user})
            
            if len(new_password) < 6:
                messages.error(request, 'Password must be at least 6 characters long.')
                return render(request, 'accounts/profile.html', {'user': user})
            
            # Change password
            user.set_password(new_password)
            user.save()
            
            # Re-login user after password change
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, user)
            
            messages.success(request, 'Profile and password updated successfully!')
        else:
            user.save()
            messages.success(request, 'Profile updated successfully!')
        
        return redirect('accounts:profile')
    
    return render(request, 'accounts/profile.html', {'user': user})


def password_reset_view(request):
    """Simple password reset using email verification."""
    from .models import User
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()

        if not all([email, new_password, confirm_password]):
            messages.error(request, 'All fields are required.')
        elif new_password != confirm_password:
            messages.error(request, 'Passwords do not match.')
        elif len(new_password) < 6:
            messages.error(request, 'Password must be at least 6 characters.')
        else:
            user = User.objects.filter(email=email).first()
            if not user:
                messages.error(request, 'No account found with this email.')
            else:
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Password reset successfully! Please login.')
                return redirect('accounts:login')
    return render(request, 'accounts/password_reset.html')


def set_language_view(request):
    """Set site language explicitly and persist in session/cookie."""
    lang = (request.POST.get("language") or "en").strip().lower()
    if lang not in {"en", "hi", "gu"}:
        lang = "en"

    next_url = (request.POST.get("next") or request.META.get("HTTP_REFERER") or "/").strip()
    request.session["django_language"] = lang
    translation.activate(lang)

    response = HttpResponseRedirect(next_url)
    response.set_cookie("django_language", lang, max_age=365 * 24 * 3600)
    return response
