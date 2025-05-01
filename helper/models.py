from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import re
import logging

logger = logging.getLogger('helper')

def validate_minimum_aps(value):
    """Validates that the minimum APS score is between 20 and 48."""
    if not 20 <= value <= 48:
        raise ValidationError('Minimum APS score must be between 20 and 48.')

class University(models.Model):
    """Represents a university with its name, minimum APS score, province, and description."""
    name = models.CharField(max_length=100, unique=True)
    minimum_aps = models.IntegerField(validators=[validate_minimum_aps])
    province = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Universities'

class DocumentUpload(models.Model):
    """Stores uploaded documents for a user, such as ID pictures or academic results."""
    DOCUMENT_TYPES = (
        ('id_picture', 'ID Picture'),
        ('grade_11_results', 'Grade 11 Results'),
        ('grade_12_results', 'Grade 12 Results'),
        ('other', 'Other'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_document_type_display()} by {self.user.username}"

    class Meta:
        ordering = ['-uploaded_at']

def validate_phone_number(value):
    """Validates that the phone number follows the format +27 followed by 9 digits."""
    pattern = r'^\+27\d{9}$'
    if not re.match(pattern, value):
        raise ValidationError('Phone number must be in the format +27 followed by 9 digits, e.g., +27123456789.')

class StudentProfile(models.Model):
    """Stores user-specific profile data, including subscription details, marks, and APS score."""
    SUBSCRIPTION_PACKAGES = (
        ('basic', 'Basic Package'),
        ('standard', 'Standard Package'),
        ('premium', 'Premium Package'),
        ('ultimate', 'Ultimate Package'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=12, validators=[validate_phone_number], blank=True, null=True)
    selected_universities = models.ManyToManyField(University, blank=True)
    marks = models.JSONField(default=dict, blank=True, null=True)
    stored_aps_score = models.IntegerField(null=True, blank=True)
    subscription_package = models.CharField(max_length=20, choices=SUBSCRIPTION_PACKAGES, default='basic')
    application_count = models.IntegerField(default=0)
    subscription_status = models.BooleanField(default=False)

    def __str__(self):
        return f"Profile of {self.user.username}"

    @property
    def aps_score(self):
        """Calculates the APS score based on marks, excluding Life Orientation."""
        if not self.marks or not isinstance(self.marks, dict) or len(self.marks) != 7:
            logger.warning(f"APS calculation for {self.user.username}: Invalid marks - {self.marks}")
            return None

        try:
            aps = 0
            for subject, mark in self.marks.items():
                if subject == 'Life Orientation':
                    continue  # Skip Life Orientation for APS
                try:
                    mark = int(mark)
                    if mark >= 80:
                        aps += 7
                    elif mark >= 70:
                        aps += 6
                    elif mark >= 60:
                        aps += 5
                    elif mark >= 50:
                        aps += 4
                    elif mark >= 40:
                        aps += 3
                    elif mark >= 30:
                        aps += 2
                    else:
                        aps += 1
                except (ValueError, TypeError):
                    logger.error(f"Invalid mark for {subject}: {mark}")
                    return None
            logger.info(f"APS calculation for {self.user.username}: Calculated APS = {aps}")
            return aps
        except Exception as e:
            logger.error(f"Error calculating APS for {self.user.username}: {str(e)}", exc_info=True)
            return None

    def save(self, *args, **kwargs):
        """Updates stored_aps_score with the calculated APS score before saving."""
        calculated_aps = self.aps_score
        self.stored_aps_score = calculated_aps if calculated_aps is not None else None
        super().save(*args, **kwargs)

    def get_application_limit(self):
        """Returns the maximum number of applications allowed based on subscription package."""
        package_limits = {
            'basic': 3,
            'standard': 5,
            'premium': 7,
            'ultimate': float('inf'),
        }
        return package_limits.get(self.subscription_package, 3)

    def can_apply(self):
        """Checks if the user can submit more applications based on their subscription."""
        if not self.subscription_status:
            return False
        return self.application_count < self.get_application_limit()

    def can_access_fee_guidance(self):
        """Checks if the user can access fee guidance based on their subscription."""
        return self.subscription_package in ['standard', 'premium', 'ultimate']

    def can_access_course_advice(self):
        """Checks if the user can access course advice based on their subscription."""
        return self.subscription_package in ['premium', 'ultimate']

    def can_access_whatsapp_chat(self):
        """Checks if the user can access WhatsApp chat based on their subscription."""
        return self.subscription_package in ['premium', 'ultimate']

    def can_access_concierge_service(self):
        """Checks if the user can access concierge service based on their subscription."""
        return self.subscription_package == 'ultimate'

    def get_service_fee(self):
        """Returns the service fee for applications, free for ultimate package."""
        if self.can_access_concierge_service():
            return 0
        return 50  # R50 per application

    class Meta:
        ordering = ['user__username']
        verbose_name = 'Student Profile'
        verbose_name_plural = 'Student Profiles'