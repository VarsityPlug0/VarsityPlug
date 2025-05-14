from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save # Import for signals
from django.dispatch import receiver # Import for signals
# Attempt to import static university data from the helper app
try:
    from helper.university_static_data import get_all_universities as get_static_universities
except ImportError:
    get_static_universities = None
    # This print statement is for server startup, not for every request.
    # Consider using Django's logging framework for more robust error indication.
    print("WARNING: Could not import static university data from helper.university_static_data.")
    print("UserProfile.get_qualified_universities will return an empty list.")

class UserProfile(models.Model):
    """
    Represents a user's profile within the varsity_plug application.
    This profile stores user-specific information like their APS score.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='varsity_plug_profile')
    aps_score = models.IntegerField(null=True, blank=True, help_text="User's calculated APS score.")

    def get_qualified_universities(self):
        """
        Returns a list of university dictionaries for which the user qualifies based on their APS score,
        using the static university data from helper.university_static_data.
        """
        if self.aps_score is not None and get_static_universities:
            all_universities = get_static_universities()
            qualified = [
                uni for uni in all_universities 
                if uni.get('minimum_aps') is not None and uni['minimum_aps'] <= self.aps_score
            ]
            # Sort by name or minimum_aps if desired
            qualified.sort(key=lambda x: (x.get('minimum_aps', 999), x.get('name', '')))
            return qualified
        return [] # Return an empty list if no APS score or static data not available

    def __str__(self):
        return f"{self.user.username}'s Profile (VarsityPlug)"

# The fallback University model defined here is now OBSOLETE if we are fully relying on static data.
# Keeping it commented out for now, but it should be removed if the static data approach is final.
# if HelperUniversity is None:  # HelperUniversity is also obsolete in this context
#     class University(models.Model):
#         name = models.CharField(max_length=255)
#         minimum_aps = models.IntegerField(help_text="Minimum APS score required for general admission.")
#         province = models.CharField(max_length=100, blank=True, null=True)
#         application_fee = models.CharField(max_length=50, blank=True, null=True, help_text="e.g., R100 or N/A")
#         due_date = models.DateField(null=True, blank=True)
#         def __str__(self):
#             return self.name
#     UserProfile._defined_university_model = University # This line is also obsolete

class Subscription(models.Model):
    """
    Represents a user's subscription status and type within the varsity_plug application.
    """
    SUBSCRIPTION_TYPES = [
        ('free', 'Free'),
        ('basic', 'Basic'),
        ('standard', 'Standard'),
        ('premium', 'Premium'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='varsity_plug_subscription')
    subscription_type = models.CharField(max_length=20, choices=SUBSCRIPTION_TYPES, default='free')
    is_active = models.BooleanField(default=False)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    def get_subscription_type_display(self):
        return dict(self.SUBSCRIPTION_TYPES).get(self.subscription_type, 'Unknown')

    def __str__(self):
        return f"{self.user.username} - {self.get_subscription_type_display()} Subscription"

class Document(models.Model):
    """
    Represents a document uploaded by a user within the varsity_plug application.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='varsity_plug_documents')
    file = models.FileField(upload_to='varsity_plug_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Document for {self.user.username} uploaded at {self.uploaded_at.strftime('%Y-%m-%d %H:%M')}"

@receiver(post_save, sender=User)
def create_user_profile_and_subscription(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)
        Subscription.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile_and_subscription(sender, instance, **kwargs):
    # Ensure related objects exist and save them.
    # Note: get_or_create in the first signal already handles creation.
    # This signal ensures that if User is saved, associated profiles are also saved if they exist.
    # However, direct saving of User instance doesn't cascade to save OneToOneField related objects automatically
    # unless the related objects themselves were modified.
    # For explicit save or complex logic, one might need this, but often not required if profile changes trigger their own saves.
    try:
        if hasattr(instance, 'varsity_plug_profile'):
             instance.varsity_plug_profile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.get_or_create(user=instance) # Ensure it exists if somehow missed
    
    try:
        if hasattr(instance, 'varsity_plug_subscription'):
            instance.varsity_plug_subscription.save()
    except Subscription.DoesNotExist:
        Subscription.objects.get_or_create(user=instance) # Ensure it exists if somehow missed 