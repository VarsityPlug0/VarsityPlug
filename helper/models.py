from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import re

class University(models.Model):
    name = models.CharField(max_length=100, unique=True)
    minimum_aps = models.IntegerField()
    province = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class DocumentUpload(models.Model):
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

def validate_phone_number(value):
    pattern = r'^\+27\d{9}$'
    if not re.match(pattern, value):
        raise ValidationError('Phone number must be in the format +27 followed by 9 digits, e.g., +27123456789.')

class StudentProfile(models.Model):
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
    subscription_package = models.CharField(max_length=20, choices=SUBSCRIPTION_PACKAGES, default='basic')
    application_count = models.IntegerField(default=0)
    subscription_status = models.BooleanField(default=False)

    def __str__(self):
        return f"Profile of {self.user.username}"

    @property
    def aps_score(self):
        if not self.marks or len(self.marks) != 7:
            print(f"APS calculation for {self.user.username}: Not enough subjects - {self.marks}")
            return None

        print(f"APS calculation for {self.user.username}: Found 7 subjects - {self.marks}")
        aps = 0
        for subject, mark in self.marks.items():
            if subject == 'Life Orientation':
                continue  # Skip Life Orientation for APS
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
        print(f"APS calculation for {self.user.username}: Calculated APS = {aps}")
        return aps

    def get_application_limit(self):
        package_limits = {
            'basic': 3,
            'standard': 5,
            'premium': 7,
            'ultimate': float('inf'),
        }
        return package_limits.get(self.subscription_package, 3)

    def can_apply(self):
        if not self.subscription_status:
            return False
        return self.application_count < self.get_application_limit()

    def can_access_fee_guidance(self):
        return self.subscription_package in ['standard', 'premium', 'ultimate']

    def can_access_course_advice(self):
        return self.subscription_package in ['premium', 'ultimate']

    def can_access_whatsapp_chat(self):
        return self.subscription_package in ['premium', 'ultimate']

    def can_access_concierge_service(self):
        return self.subscription_package == 'ultimate'

    def get_service_fee(self):
        if self.can_access_concierge_service():
            return 0
        return 50  # R50 per application