from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("", views.login_view, name="login"),
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("redirect/", views.role_redirect_view, name="role_redirect"),
    path("profile/", views.profile_view, name="profile"),
    path("set-language/", views.set_language_view, name="set_language"),
    path("password-reset/", views.password_reset_view, name="password_reset"),
]
