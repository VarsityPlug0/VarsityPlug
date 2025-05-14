import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'varsity_plug.settings')
django.setup()

from helper.models import StudentProfile
from django.contrib.auth.models import User

# Get all student profiles
profiles = StudentProfile.objects.all()
print(f"Total profiles: {profiles.count()}")

# Check each profile
for profile in profiles:
    print(f"\nProfile for user: {profile.user.username}")
    print(f"Selected universities: {profile.selected_universities}")
    print(f"Subscription package: {profile.subscription_package}")
    print(f"Application count: {profile.application_count}")
    print(f"Marks: {profile.marks}")
    print(f"Stored APS score: {profile.stored_aps_score}")
    print(f"WhatsApp enabled: {profile.whatsapp_enabled}")
    print(f"Last chat date: {profile.last_chat_date}") 