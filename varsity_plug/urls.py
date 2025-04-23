from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LogoutView
from django.conf import settings
from django.conf.urls.static import static
from django.views.defaults import page_not_found

# Define the URL patterns
urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # Include URLs from the 'helper' app with namespace
    path('', include('helper.urls', namespace='helper')),
    
    # Django's built-in authentication URLs (login, password reset, etc.)
    path('accounts/', include('django.contrib.auth.urls')),
    
    # Custom logout view that redirects to the home page
    path('accounts/logout/', LogoutView.as_view(next_page='helper:home'), name='logout'),
]

# Serve static files during development (only when DEBUG is True)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom 404 handler
handler404 = page_not_found