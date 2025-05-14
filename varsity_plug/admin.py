from django.contrib import admin
from .models import UserProfile, Subscription, Document

# Try to import the University model (either HelperUniversity or the fallback)
# This logic mirrors what's in models.py to determine which University model to register.
try:
    from helper.models import University as ActualUniversity # Attempt to import the primary University model
except ImportError:
    # If helper.models.University can't be imported, and UserProfile._defined_university_model exists,
    # it means the fallback University model was defined in varsity_plug.models
    if hasattr(UserProfile, '_defined_university_model'):
        ActualUniversity = UserProfile._defined_university_model
    else:
        ActualUniversity = None # No University model could be determined

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'aps_score')
    search_fields = ('user__username', 'user__email')

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscription_type', 'is_active', 'start_date', 'end_date')
    list_filter = ('subscription_type', 'is_active')
    search_fields = ('user__username',)

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('user', 'description', 'uploaded_at')
    search_fields = ('user__username', 'description')
    list_filter = ('uploaded_at',)

# Register the University model if it was successfully determined
if ActualUniversity:
    @admin.register(ActualUniversity)
    class UniversityAdmin(admin.ModelAdmin):
        list_display = ('name', 'minimum_aps', 'province', 'application_fee', 'due_date')
        search_fields = ('name', 'province')
        list_filter = ('province', 'minimum_aps')
else:
    print("Could not determine University model to register for Django Admin in varsity_plug.") 