"""
Main URL configuration. Includes accounts, student, counsellor, admin_panel.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from student import views as student_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('', include('accounts.urls')),
    path('student/community/posts/<str:post_id>/delete/', student_views.delete_daily_post_view, name='delete_daily_post'),
    path('student/', include('student.urls')),
    path('counsellor/', include('counsellor.urls')),
    path('admin_panel/', include('admin_panel.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
