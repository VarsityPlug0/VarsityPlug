from django.contrib import admin
from .models import University, DocumentUpload, StudentProfile, ApplicationStatus, Payment
from .university_static_data import get_university_by_id

@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ('name', 'province', 'minimum_aps', 'application_fee', 'due_date')
    list_filter = ('province', 'minimum_aps')
    search_fields = ('name', 'description')
    ordering = ('name',)

@admin.register(DocumentUpload)
class DocumentUploadAdmin(admin.ModelAdmin):
    list_display = ('user', 'document_type', 'university', 'uploaded_at', 'verified', 'verification_date')
    list_filter = ('document_type', 'verified', 'uploaded_at')
    search_fields = ('user__username', 'university__name')
    ordering = ('-uploaded_at',)
    raw_id_fields = ('user', 'university')

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscription_package', 'stored_aps_score', 'application_count', 'whatsapp_enabled')
    list_filter = ('subscription_package', 'whatsapp_enabled')
    search_fields = ('user__username', 'user__email', 'phone_number')
    raw_id_fields = ('user',)
    readonly_fields = ('stored_aps_score',)

@admin.register(ApplicationStatus)
class ApplicationStatusAdmin(admin.ModelAdmin):
    def university_name(self, obj):
        uni = get_university_by_id(obj.university_id)
        return uni['name'] if uni else 'Unknown'
    university_name.short_description = 'University'

    list_display = ('student', 'university_name', 'status', 'application_date', 'last_updated', 'payment_verified')
    list_filter = ('status', 'payment_verified', 'application_date')
    search_fields = ('student__user__username', 'tracking_number')
    raw_id_fields = ('student',)
    ordering = ('-application_date',)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'university', 'amount', 'payment_status', 'upload_date', 'verification_date')
    list_filter = ('payment_status', 'upload_date')
    search_fields = ('user__username', 'university')
    raw_id_fields = ('user',)
    ordering = ('-upload_date',)
