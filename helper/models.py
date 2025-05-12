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
    application_fee = models.CharField(max_length=100, default="FREE")
    due_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Universities'

class DocumentUpload(models.Model):
    """Stores uploaded documents for a user, such as ID pictures, academic results, or proof of payment."""
    DOCUMENT_TYPES = [
        ('id_picture', 'ID Picture'),
        ('grade_11_results', 'Grade 11 Results'),
        ('grade_12_results', 'Grade 12 Results'),
        ('payment_proof', 'Proof of Payment'),
        ('subscription_payment', 'Subscription Payment'),
        ('other', 'Other')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    university = models.ForeignKey(University, on_delete=models.SET_NULL, null=True, blank=True)
    verified = models.BooleanField(default=False)
    verification_date = models.DateTimeField(null=True, blank=True)  # Track when the document was verified
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s {self.get_document_type_display()}"

    class Meta:
        ordering = ['-uploaded_at']

def validate_phone_number(value):
    """Validates that the phone number follows the format +27 followed by 9 digits."""
    pattern = r'^\+27\d{9}$'
    if not re.match(pattern, value):
        raise ValidationError('Phone number must be in the format +27 followed by 9 digits, e.g., +27123456789.')

class StudentProfile(models.Model):
    """Represents a student's profile with subscription and application information."""
    SUBSCRIPTION_PACKAGES = [
        ('basic', 'Basic'),
        ('standard', 'Standard'),
        ('premium', 'Premium'),
        ('ultimate', 'Ultimate')
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    subscription_package = models.CharField(max_length=20, choices=SUBSCRIPTION_PACKAGES, default='basic')
    application_count = models.IntegerField(default=0)
    selected_universities = models.ManyToManyField(University, blank=True)
    marks = models.JSONField(null=True, blank=True)
    stored_aps_score = models.IntegerField(null=True, blank=True)
    whatsapp_enabled = models.BooleanField(default=False)
    last_chat_date = models.DateTimeField(null=True, blank=True)

    @property
    def subscription_status(self):
        """Dynamically checks if the subscription is active based on verified payment proof."""
        subscription_payment_doc = self.user.documentupload_set.filter(document_type='subscription_payment').first()
        if subscription_payment_doc and subscription_payment_doc.verified:
            return True  # Active
        return False # Not Paid (or pending verification, or proof deleted)

    def get_subscription_fee(self):
        """Return the subscription fee based on the package."""
        fees = {
            'basic': 400,
            'standard': 600,
            'premium': 800,
            'ultimate': 1000
        }
        return fees.get(self.subscription_package, 0)

    def get_application_limit(self):
        """Return the application limit based on subscription package."""
        # R100 per application, Ultimate is unlimited
        # Using a large number for unlimited to simplify checks elsewhere.
        limits = {
            'basic': 4,     # R400 / R100 = 4 applications
            'standard': 6,  # R600 / R100 = 6 applications
            'premium': 8,   # R800 / R100 = 8 applications
            'ultimate': 999 # Effectively unlimited
        }
        return limits.get(self.subscription_package, 0) # Default to 0 if package not found

    def can_apply(self):
        """Check if the student can apply to more universities."""
        return self.application_count < self.get_application_limit()

    def can_access_whatsapp_chat(self):
        """Check if the student can access WhatsApp chat."""
        return self.subscription_package in ['premium', 'ultimate']

    def can_access_course_advice(self):
        """Check if the student can access course advice."""
        return self.subscription_package in ['premium', 'ultimate']

    def can_access_fee_guidance(self):
        """Check if the student can access fee guidance."""
        return self.subscription_package in ['standard', 'premium', 'ultimate']

    def can_access_concierge_service(self):
        """Check if the student can access concierge service."""
        return self.subscription_package == 'ultimate'

    def __str__(self):
        return f"{self.user.username}'s Profile"

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
                    continue
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
        self.stored_aps_score = calculated_aps if calculated_aps is not None else 0
        super().save(*args, **kwargs)

    def get_service_fee(self):
        """Returns the service fee for applications, free for ultimate package."""
        if self.can_access_concierge_service():
            return 0
        return 50

    class Meta:
        ordering = ['user__username']
        verbose_name = 'Student Profile'
        verbose_name_plural = 'Student Profiles'

class ApplicationStatus(models.Model):
    """Tracks the status of university applications."""
    STATUS_CHOICES = (
        ('not_started', 'Not Started'),
        ('pending', 'Pending'),
        ('submitted', 'Submitted'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    )
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    university = models.ForeignKey(University, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    application_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True)
    payment_verified = models.BooleanField(default=False)
    tracking_number = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.student.user.username}'s application to {self.university.name}"

    class Meta:
        ordering = ['-application_date']
        unique_together = ('student', 'university')
        verbose_name = 'Application Status'
        verbose_name_plural = 'Application Statuses'

class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('not_paid', 'Not Paid'),
        ('pending', 'Pending Verification'),
        ('paid', 'Paid'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    university = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='not_paid')
    proof_of_payment = models.FileField(upload_to='payment_proofs/', null=True, blank=True)
    upload_date = models.DateTimeField(auto_now_add=True)
    verification_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.university} - {self.payment_status}"
    
    class Meta:
        ordering = ['-upload_date']