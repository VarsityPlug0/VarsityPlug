from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import DocumentUpload, StudentProfile, University
from django.core.exceptions import ValidationError

class ExtendedUserCreationForm(UserCreationForm):
    """Extended user registration form with email field."""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user

class DocumentUploadForm(forms.ModelForm):
    """Form for uploading documents."""
    class Meta:
        model = DocumentUpload
        fields = ['document_type', 'file', 'university']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'document_type': forms.Select(attrs={'class': 'form-control'}),
            'university': forms.Select(attrs={'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Use the model's document type choices
        self.fields['document_type'].choices = DocumentUpload.DOCUMENT_TYPES
        # Make university field optional
        self.fields['university'].required = False

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            if file.size > 5 * 1024 * 1024:  # 5MB limit
                raise ValidationError('File size must be under 5MB.')
            ext = file.name.split('.')[-1].lower()
            if ext not in ['pdf', 'jpg', 'jpeg', 'png']:
                raise ValidationError('Only PDF, JPG, JPEG, and PNG files are allowed.')
        return file

class MarksForm(forms.Form):
    """Form for entering subject marks."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .views import NSC_SUBJECTS
        
        # Add compulsory subjects first
        for subject in NSC_SUBJECTS['compulsory']:
            self.fields[subject] = forms.IntegerField(
                required=False,
                min_value=0,
                max_value=100,
                widget=forms.NumberInput(attrs={
                    'class': 'form-control',
                    'placeholder': '0-100'
                })
            )
        
        # Add elective subjects
        for subject in NSC_SUBJECTS['elective']:
            self.fields[subject] = forms.IntegerField(
                required=False,
                min_value=0,
                max_value=100,
                widget=forms.NumberInput(attrs={
                    'class': 'form-control',
                    'placeholder': '0-100'
                })
            )

    def clean(self):
        cleaned_data = super().clean()
        marks = {k: v for k, v in cleaned_data.items() if v is not None}
        
        # Check for required compulsory subjects
        required_compulsory = [
            "Life Orientation",
            "Mathematics" if "Mathematics" in marks else "Mathematical Literacy"
        ]
        
        for subject in required_compulsory:
            if subject not in marks:
                raise ValidationError(f'{subject} mark is required.')
        
        # Check for at least one language subject
        language_subjects = [s for s in marks.keys() if "Language" in s]
        if not language_subjects:
            raise ValidationError('At least one language subject is required.')
        
        # Check for total number of subjects (7)
        if len(marks) != 7:
            raise ValidationError('Please enter exactly 7 subject marks.')
        
        return marks

class StudentProfileForm(forms.ModelForm):
    """Form for updating student profile information."""
    class Meta:
        model = StudentProfile
        fields = ['phone_number']
        widgets = {
            'phone_number': forms.TextInput(attrs={'placeholder': '+27123456789'})
        }

class UniversitySearchForm(forms.Form):
    """Form for searching universities."""
    search = forms.CharField(required=False)
    province = forms.ChoiceField(
        required=False,
        choices=[('', 'All Provinces')] + [
            ('Eastern Cape', 'Eastern Cape'),
            ('Free State', 'Free State'),
            ('Gauteng', 'Gauteng'),
            ('KwaZulu-Natal', 'KwaZulu-Natal'),
            ('Limpopo', 'Limpopo'),
            ('Mpumalanga', 'Mpumalanga'),
            ('North West', 'North West'),
            ('Northern Cape', 'Northern Cape'),
            ('Western Cape', 'Western Cape'),
        ]
    )
    min_aps = forms.IntegerField(required=False, min_value=20, max_value=48)

class ChatForm(forms.Form):
    """Form for AI chat interactions."""
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'form-control',
            'placeholder': 'Ask me anything about university applications...'
        }),
        max_length=500
    )

class ApplicationStatusForm(forms.Form):
    """Form for updating application status."""
    PAYMENT_CHOICES = [
        ('not_paid', 'Not Paid'),
        ('pending_verification', 'Pending Verification'),
        ('verified', 'Payment Verified')
    ]
    
    payment_status = forms.ChoiceField(choices=PAYMENT_CHOICES)
    tracking_number = forms.CharField(required=False)
    notes = forms.CharField(widget=forms.Textarea, required=False)

class DocumentVerificationForm(forms.Form):
    """Form for verifying uploaded documents."""
    verified = forms.BooleanField(required=False)
    notes = forms.CharField(widget=forms.Textarea, required=False)

class UniversitySelectionForm(forms.Form):
    """Form for selecting universities to apply to."""
    universities = forms.ModelMultipleChoiceField(
        queryset=University.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )

    def __init__(self, *args, student=None, **kwargs):
        super().__init__(*args, **kwargs)
        if student:
            # Filter universities based on student's APS score
            self.fields['universities'].queryset = University.objects.filter(
                minimum_aps__lte=student.stored_aps_score
            )

class WhatsAppEnableForm(forms.Form):
    """Form for enabling WhatsApp notifications."""
    enable_whatsapp = forms.BooleanField(required=False)
    phone_number = forms.CharField(
        validators=[StudentProfile.phone_number.field.validators],
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '+27123456789'})
    )

    def clean(self):
        cleaned_data = super().clean()
        enable_whatsapp = cleaned_data.get('enable_whatsapp')
        phone_number = cleaned_data.get('phone_number')
        
        if enable_whatsapp and not phone_number:
            raise ValidationError('Phone number is required to enable WhatsApp notifications.')