# varsity_plug/urls.py
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.views import LogoutView  # Import LogoutView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('helper.urls')),  # Main app routes
    path('accounts/', include('django.contrib.auth.urls')),  # Built-in login, logout, password reset, etc.
    path('accounts/logout/', LogoutView.as_view(next_page='home'), name='logout'),  # Custom logout redirect to home
]
