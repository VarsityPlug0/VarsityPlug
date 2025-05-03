from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LogoutView
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
    path('', include('helper.urls', namespace='helper')),
    # Django's built-in authentication URLs (login, password reset, etc.)
    path('accounts/', include('django.contrib.auth.urls')),
    # Custom logout view that redirects to the home page
    path('accounts/logout/', LogoutView.as_view(next_page='helper:home'), name='logout'),
]

# Serve static and media files during development (only when DEBUG is True)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom 404 handler
handler404 = 'helper.views.custom_404'