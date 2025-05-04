from django.urls import path
from . import views

# Set the app namespace for URL names
app_name = 'helper'

urlpatterns = [
    # Health Check
    path('health/', views.health_check, name='health_check'),  # Health check endpoint for deployment monitoring

    # Home
    path('', views.home, name='home'),  # Landing page for VarsityPlugApp

    # Static Pages
    path('about/', views.about, name='about'),  # About page
    path('services/', views.services, name='services'),  # Services page
    path('contact/', views.contact, name='contact'),  # Contact page

    # User Authentication and Registration
    path('register/', views.register, name='register'),  # User registration
    path('redirect_after_login/', views.redirect_after_login, name='redirect_after_login'),  # Redirects after login based on user role

    # Subscription Selection
    path('subscription/', views.subscription_selection, name='subscription_selection'),  # Choose or upgrade subscription package

    # Dashboards
    path('dashboard/student/', views.dashboard_student, name='dashboard_student'),  # Student dashboard with marks, documents, and university selection
    path('dashboard/guide/', views.dashboard_guide, name='dashboard_guide'),  # Guide dashboard (for non-students)

    # Document Management
    path('document/delete/<int:doc_id>/', views.delete_document, name='delete_document'),  # Delete uploaded document
    path('document/edit/<int:doc_id>/', views.edit_document, name='edit_document'),  # Edit uploaded document

    # University-Related Views
    path('universities/', views.universities_list, name='universities_list'),  # List all universities with selection options
    path('university/<int:uni_id>/', views.university_detail, name='university_detail'),  # View university details
    path('university/<int:uni_id>/faculties/', views.university_faculties, name='university_faculties'),  # View university faculties and courses
    path('select-university/<int:uni_id>/', views.select_university, name='select_university'),  # Select a university for application

    # Payment-Related Views
    path('pay/<int:uni_id>/', views.pay_application_fee, name='pay_application_fee'),  # Initiate payment for a single university
    path('pay/<int:uni_id>/instructions/', views.pay_application_fee_instructions, name='pay_application_fee_instructions'),  # Payment instructions for a single university
    path('pay/all/', views.pay_all_application_fees, name='pay_all_application_fees'),  # Pay fees for all selected universities

    # AI Chat Endpoint
    path('ai-chat/', views.ai_chat, name='ai_chat'),  # Handle AI chat requests for the chat widget
]