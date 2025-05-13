from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from helper.views import custom_404  # Assuming a custom 404 view in helper app

# Health check endpoint for Render
def health_check(request):
    return HttpResponse("OK", status=200)

# Define the URL patterns
urlpatterns = [
    # Health check for Render
    path('health/', health_check, name='health_check'),
    # Admin interface
    path('admin/', admin.site.urls),
    # Include URLs from the 'helper' app with namespace
    path('', include('helper.urls')),
    # Django's built-in authentication URLs (login, password reset, etc.)
    path('login/', auth_views.LoginView.as_view(template_name='helper/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='helper:home'), name='logout'),
    path('password-reset/',
         auth_views.PasswordResetView.as_view(template_name='helper/password_reset.html'),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='helper/password_reset_done.html'),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='helper/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='helper/password_reset_complete.html'),
         name='password_reset_complete'),
]

# Serve static and media files during development (only when DEBUG is True)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom 404 handler
handler404 = 'helper.views.custom_404'