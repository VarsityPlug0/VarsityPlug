from django.urls import path
from . import views

# Set the app namespace for URL names
app_name = 'helper'

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('services/', views.services, name='services'),
    path('contact/', views.contact, name='contact'),
    path('health/', views.health_check, name='health_check'),

    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('redirect-after-login/', views.redirect_after_login, name='redirect_after_login'),
    path('subscription-selection/', views.subscription_selection, name='subscription_selection'),

    # Student dashboard and profile
    path('dashboard/', views.dashboard_student, name='dashboard_student'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('profile/marks/', views.update_marks, name='update_marks'),
    path('profile/whatsapp/', views.whatsapp_settings, name='whatsapp_settings'),

    # Documents
    path('documents/upload/', views.upload_document, name='upload_document'),
    path('documents/list/', views.document_list, name='document_list'),
    path('documents/<int:doc_id>/delete/', views.delete_document, name='delete_document'),
    path('documents/<int:doc_id>/edit/', views.edit_document, name='edit_document'),
    path('documents/<int:doc_id>/verify/', views.verify_document, name='verify_document'),

    # Universities
    path('universities/', views.universities_list, name='universities_list'),
    path('universities/api/', views.universities_api, name='universities_api'),
    path('universities/<int:uni_id>/', views.university_detail, name='university_detail'),
    path('universities/<int:uni_id>/faculties/', views.university_faculties, name='university_faculties'),
    path('universities/<int:uni_id>/select/', views.select_university, name='select_university'),
    path('universities/<int:uni_id>/deselect/', views.deselect_university, name='deselect_university'),

    # Applications
    path('applications/', views.application_list, name='application_list'),
    path('applications/<int:app_id>/', views.application_detail, name='application_detail'),
    path('applications/<int:app_id>/status/', views.update_application_status, name='update_application_status'),
    path('applications/pay/<int:uni_id>/', views.pay_application_fee, name='pay_application_fee'),
    path('applications/pay/<int:uni_id>/instructions/', views.pay_application_fee_instructions, name='pay_application_fee_instructions'),
    path('applications/pay/all/', views.pay_all_application_fees, name='pay_all_application_fees'),
    path('applications/pay/<int:university_id>/', views.pay_application_fee, name='pay_application_fee'),
    path('applications/payment-proof/<int:application_id>/', views.view_payment_proof, name='view_payment_proof'),
    path('payments/', views.payments, name='payments'),
    path('payments/unified/', views.unified_payment, name='unified_payment'),

    # AI Chat
    path('chat/', views.ai_chat, name='ai_chat'),
    path('chat/history/', views.chat_history, name='chat_history'),

    # Course Advice
    path('course-advice/', views.course_advice, name='course_advice'),
    path('course-advice/<int:uni_id>/', views.university_course_advice, name='university_course_advice'),

    # Fee Guidance
    path('fee-guidance/', views.fee_guidance, name='fee_guidance'),
    path('fee-guidance/<int:uni_id>/', views.university_fee_guidance, name='university_fee_guidance'),

    # Concierge Service
    path('concierge/', views.concierge_service, name='concierge_service'),
    path('concierge/request/', views.concierge_request, name='concierge_request'),

    # API endpoints
    path('api/universities/search/', views.university_search_api, name='university_search_api'),
    path('api/chat/message/', views.chat_message_api, name='chat_message_api'),
    path('api/documents/verify/', views.verify_document_api, name='verify_document_api'),
    path('edit-marks/', views.edit_marks, name='edit_marks'),
    path('pay-subscription-fee/', views.pay_subscription_fee, name='pay_subscription_fee'),
    path('upgrade-subscription/', views.upgrade_subscription, name='upgrade_subscription'),
    path('upload-payment-proof/', views.upload_payment_proof, name='upload_payment_proof'),
]