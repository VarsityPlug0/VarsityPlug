from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils.safestring import mark_safe
from django.urls import reverse
from .forms import DocumentUploadForm, MarksForm
from .models import DocumentUpload, University, StudentProfile, Payment
from .faculty_data import FACULTY_COURSES, FACULTIES_OPEN
from django_ratelimit.decorators import ratelimit
from django.http import JsonResponse, HttpResponse, HttpResponseNotFound, HttpResponseNotAllowed, HttpResponseBadRequest
from django.utils.html import escape
import openai
from django.conf import settings
import logging
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from .models import ApplicationStatus
from .forms import (
    ExtendedUserCreationForm, StudentProfileForm, UniversitySearchForm, ChatForm,
    ApplicationStatusForm, DocumentVerificationForm, UniversitySelectionForm, WhatsAppEnableForm
)
import time
from .utils import calculate_application_fees

# Set up logging
logger = logging.getLogger(__name__)

# Set up OpenAI API key
if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
    openai.api_key = settings.OPENAI_API_KEY
else:
    logger.critical("OPENAI_API_KEY is not set in settings. AI chat functionality will fail.")

# Valid NSC subjects
NSC_SUBJECTS = {
    'compulsory': [
        "English Home Language",
        "English First Additional Language",
        "Afrikaans Home Language",
        "Afrikaans First Additional Language",
        "IsiNdebele Home Language",
        "IsiNdebele First Additional Language",
        "IsiXhosa Home Language",
        "IsiXhosa First Additional Language",
        "IsiZulu Home Language",
        "IsiZulu First Additional Language",
        "Sepedi Home Language",
        "Sepedi First Additional Language",
        "Sesotho Home Language",
        "Sesotho First Additional Language",
        "Setswana Home Language",
        "Setswana First Additional Language",
        "Siswati Home Language",
        "Siswati First Additional Language",
        "Tshivenda Home Language",
        "Tshivenda First Additional Language",
        "Xitsonga Home Language",
        "Xitsonga First Additional Language",
        "Life Orientation",
        "Mathematics",
        "Mathematical Literacy"
    ],
    'elective': [
        "Accounting",
        "Agricultural Sciences",
        "Business Studies",
        "Consumer Studies",
        "Dramatic Arts",
        "Economics",
        "Engineering Graphics and Design",
        "Geography",
        "History",
        "Information Technology",
        "Life Sciences",
        "Music",
        "Physical Sciences",
        "Tourism",
        "Visual Arts",
        "Computer Applications Technology",
        "Religion Studies"
    ]
}

# Constants for University Info
UNIVERSITY_DUE_DATES = {
    "Cape Peninsula University of Technology (CPUT)": "2025-09-30",
    "Central University of Technology (CUT)": "2025-10-31",
    "Durban University of Technology (DUT)": "2025-09-30",
    "Mangosuthu University of Technology (MUT)": "2025-02-28",
    "Nelson Mandela University (NMU)": "2025-09-30",
    "North-West University (NWU)": "2025-06-30",
    "Rhodes University (RU)": "2025-09-30",
    "Sefako Makgatho Health Sciences University (SMU)": "2025-06-28",
    "Sol Plaatje University (SPU)": "2025-10-31",
    "Stellenbosch University (SU)": "2025-07-31",
    "Tshwane University of Technology (TUT)": "2025-09-30",
    "University of Cape Town (UCT)": "2025-07-31",
    "University of Fort Hare (UFH)": "2025-09-30",
    "University of Johannesburg (UJ)": "2025-10-31",
    "University of KwaZulu-Natal (UKZN)": "2025-06-30",
    "University of Limpopo (UL)": "2025-09-30",
    "University of Mpumalanga (UMP)": "2025-01-30",
    "University of Pretoria (UP)": "2025-06-30",
    "University of South Africa (UNISA)": "2025-10-11",
    "University of the Free State (UFS)": "2025-09-30",
    "University of the Western Cape (UWC)": "2025-09-30",
    "University of the Witwatersrand (Wits)": "2025-09-30",
    "University of Venda (Univen)": "2025-09-27",
    "University of Zululand (UniZulu)": "2025-10-31",
    "Vaal University of Technology (VUT)": "2025-09-30",
    "Walter Sisulu University (WSU)": "2025-10-31",
}

APPLICATION_FEES_2025 = {
    "Cape Peninsula University of Technology (CPUT)": "R100",
    "Central University of Technology (CUT)": "FREE (online), R245 (manual via CAO)",
    "Durban University of Technology (DUT)": "R250 (on-time), R470 (late)",
    "Mangosuthu University of Technology (MUT)": "R250 (on-time), R470 (late)",
    "Nelson Mandela University (NMU)": "FREE",
    "North-West University (NWU)": "FREE",
    "Rhodes University (RU)": "R100",
    "Sefako Makgatho Health Sciences University (SMU)": "R200",
    "Sol Plaatje University (SPU)": "FREE",
    "Stellenbosch University (SU)": "R100",
    "Tshwane University of Technology (TUT)": "R240",
    "University of Cape Town (UCT)": "R100",
    "University of Fort Hare (UFH)": "FREE",
    "University of Johannesburg (UJ)": "FREE (online), R200 (manual)",
    "University of KwaZulu-Natal (UKZN)": "R210 (on-time), R420 (late)",
    "University of Limpopo (UL)": "R200",
    "University of Mpumalanga (UMP)": "R150",
    "University of Pretoria (UP)": "R300",
    "University of South Africa (UNISA)": "R135",
    "University of the Free State (UFS)": "R100",
    "University of the Western Cape (UWC)": "FREE",
    "University of the Witwatersrand (Wits)": "R100",
    "University of Venda (Univen)": "R100",
    "University of Zululand (UniZulu)": "R220 (on-time), R440 (late)",
    "Vaal University of Technology (VUT)": "R150",
    "Walter Sisulu University (WSU)": "FREE",
}

def calculate_aps(marks):
    """Calculate APS score based on NSC marks, excluding Life Orientation."""
    if not marks or not isinstance(marks, dict) or len(marks) != 7:
        return None

    aps = 0
    subjects_processed = set()

    for subject, mark in marks.items():
        if subject in subjects_processed:
            continue

        if mark is None:
            return None

        try:
            mark_num = float(mark)
        except (ValueError, TypeError):
            return None

        if not 0 <= mark_num <= 100:
            return None

        # Skip Life Orientation in APS calculation
        if subject == 'Life Orientation':
            subjects_processed.add(subject)
            continue

        # Calculate points based on mark ranges
        if mark_num >= 80:
            aps += 7
        elif mark_num >= 70:
            aps += 6
        elif mark_num >= 60:
            aps += 5
        elif mark_num >= 50:
            aps += 4
        elif mark_num >= 40:
            aps += 3
        elif mark_num >= 30:
            aps += 2
        else:
            aps += 1

        subjects_processed.add(subject)

    # Ensure all required subjects are present
    if len(subjects_processed) != 7 or 'Life Orientation' not in subjects_processed:
        return None

    return aps

def custom_404(request, exception):
    """Handle 404 errors with a custom page."""
    return render(request, '404.html', status=404)

def health_check(request):
    """Render health check endpoint for deployment monitoring."""
    return HttpResponse("OK", status=200)

def home(request):
    """Render the homepage."""
    return render(request, 'helper/home.html', {'title': 'Welcome to Varsity Plug'})

def about(request):
    """Render the about page."""
    return render(request, 'helper/about.html', {'title': 'About Us'})

def services(request):
    """Render the services page."""
    return render(request, 'helper/services.html', {'title': 'Our Services'})

def contact(request):
    """Render the contact page."""
    return render(request, 'helper/contact.html', {'title': 'Contact Us'})

def is_logged_out(user):
    """Check if user is logged out."""
    return not user.is_authenticated

@user_passes_test(is_logged_out, login_url='helper:dashboard_student')
def register(request):
    """Handle user registration."""
    if request.method == 'POST':
        form = ExtendedUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create StudentProfile with default package
            StudentProfile.objects.create(
                user=user,
                subscription_package='basic'  # Set default package to basic
            )
            login(request, user)
            messages.success(request, "Registration successful! Welcome to Varsity Plug.")
            return redirect('helper:subscription_selection')
    else:
        form = ExtendedUserCreationForm()
    return render(request, 'helper/register.html', {'form': form})

@user_passes_test(is_logged_out, login_url='helper:dashboard_student')
def login_view(request):
    """Handle user login."""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, "Login successful!")
            return redirect('helper:redirect_after_login')
    else:
        form = AuthenticationForm()
    return render(request, 'helper/login.html', {'form': form})

@login_required
def logout_view(request):
    """Handle user logout."""
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect('helper:home')

@login_required
def redirect_after_login(request):
    """Redirect users after login based on their subscription status."""
    try:
        profile = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        # Create a new profile with default values
        profile = StudentProfile.objects.create(
            user=request.user,
            subscription_package='basic'  # Set default package to basic
        )
    
    # Check subscription status using the property method
    try:
        if not profile.subscription_status:
            return redirect('helper:subscription_selection')
    except Exception:
        # If there's any error checking subscription status, redirect to subscription selection
        return redirect('helper:subscription_selection')
    
    return redirect('helper:dashboard_student')

@login_required
def subscription_selection(request):
    """View for selecting subscription package"""
    if request.method == 'POST':
        package = request.POST.get('package')
        if package:
            # Get or create student profile
            profile, created = StudentProfile.objects.get_or_create(user=request.user)
            # Update subscription package
            profile.subscription_package = package
            profile.save()
            
            # Check for existing subscription payment
            subscription_payment = DocumentUpload.objects.filter(
                user=request.user,
                document_type='subscription_payment'
            ).first()
            
            if subscription_payment:
                time_since_upload = timezone.now() - subscription_payment.uploaded_at
                if time_since_upload.total_seconds() >= 86400:  # 24 hours
                    subscription_payment.verified = True
                    subscription_payment.save()
                    messages.success(request, 'Your subscription has been activated!')
                else:
                    messages.info(request, 'Your subscription payment is pending verification.')
            else:
                messages.info(request, 'Please upload your payment proof to activate your subscription.')
            return redirect('helper:pay_subscription_fee')

    # Build the correct package list
    packages = [
        {
            'value': 'basic',
            'name': 'Basic Package',
            'price': 'R400',
            'includes': 'Access to university applications, Basic application tracking, Email support'
        },
        {
            'value': 'standard',
            'name': 'Standard Package',
            'price': 'R600',
            'includes': 'All Basic features, Priority application processing, Document verification, 24/7 support'
        },
        {
            'value': 'premium',
            'name': 'Premium Package',
            'price': 'R800',
            'includes': 'All Standard features, Personal application advisor, Expedited processing, Priority support, Application review'
        },
        {
            'value': 'ultimate',
            'name': 'Ultimate Package',
            'price': 'R1000',
            'includes': 'All Premium features, Unlimited applications, Concierge service, 24/7 priority support'
        }
    ]

    return render(request, 'helper/subscription_selection.html', {
        'packages': packages,
    })

@login_required
def dashboard_student(request):
    """Render student dashboard."""
    profile = get_object_or_404(StudentProfile, user=request.user)
    applications = ApplicationStatus.objects.filter(student=profile)
    documents = DocumentUpload.objects.filter(user=request.user)
    
    # Initialize the document upload form
    form = DocumentUploadForm()
    
    # Prepare marks list for the template
    marks_list = []
    if profile.marks:
        for subject, mark in profile.marks.items():
            marks_list.append({
                'subject': subject,
                'mark': mark
            })
    else:
        marks_list = [{'subject': None, 'mark': None} for _ in range(7)]
    
    # Get recommended universities based on APS score
    recommended_universities = []
    qualified_universities = []
    if profile.stored_aps_score:
        # Get universities that match the student's APS score
        qualified_universities = University.objects.filter(
            minimum_aps__lte=profile.stored_aps_score
        ).order_by('minimum_aps')
        
        # Get recommended universities (top 5 that haven't been selected)
        recommended_universities = qualified_universities.exclude(
            id__in=profile.selected_universities.values_list('id', flat=True)
        )[:5]
        
        # Add additional data to recommended universities
        for uni in recommended_universities:
            uni.detail_url = reverse('helper:university_detail', args=[uni.id])
            uni.select_url = reverse('helper:select_university', args=[uni.id])
            uni.due_date = UNIVERSITY_DUE_DATES.get(uni.name, "Not specified")
            uni.application_fee = APPLICATION_FEES_2025.get(uni.name, "Not available")
    
    # Prepare qualified universities data for JavaScript
    qualified_unis_data = []
    for uni in qualified_universities:
        qualified_unis_data.append({
            'id': uni.id,
            'name': uni.name,
            'description': uni.description,
            'minimum_aps': uni.minimum_aps,
            'province': uni.province,
            'due_date': UNIVERSITY_DUE_DATES.get(uni.name, "Not specified"),
            'application_fee': APPLICATION_FEES_2025.get(uni.name, "Not available"),
            'detail_url': reverse('helper:university_detail', args=[uni.id]),
            'select_url': reverse('helper:select_university', args=[uni.id])
        })
    
    context = {
        'profile': profile,
        'applications': applications,
        'documents': documents,
        'form': form,
        'title': 'Dashboard',
        'marks_list': marks_list,
        'nsc_subjects': NSC_SUBJECTS,
        'student_aps': profile.stored_aps_score,
        'recommended_universities': recommended_universities,
        'universities': json.dumps(qualified_unis_data, cls=DjangoJSONEncoder),
        'selected_universities': [{
            'id': uni.id,
            'name': uni.name,
            'due_date': UNIVERSITY_DUE_DATES.get(uni.name, "Not specified"),
            'application_fee': APPLICATION_FEES_2025.get(uni.name, "Not available")
        } for uni in profile.selected_universities.all()]
    }
    return render(request, 'helper/dashboard_student.html', context)

@login_required
def update_profile(request):
    """Handle student profile updates."""
    profile = get_object_or_404(StudentProfile, user=request.user)
    if request.method == 'POST':
        form = StudentProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('helper:dashboard_student')
    else:
        form = StudentProfileForm(instance=profile)
    return render(request, 'helper/update_profile.html', {'form': form})

@login_required
def update_marks(request):
    """Handle student marks updates."""
    profile = get_object_or_404(StudentProfile, user=request.user)
    if request.method == 'POST':
        # Get all subject and mark pairs from the form
        marks = {}
        for i in range(7):
            subject = request.POST.get(f'subject_{i}')
            mark = request.POST.get(f'mark_{i}')
            if subject and mark:
                try:
                    mark = int(mark)
                    if 0 <= mark <= 100:
                        marks[subject] = mark
                except (ValueError, TypeError):
                    continue

        # Validate marks
        if len(marks) != 7:
            messages.error(request, "Please enter exactly 7 subject marks.")
            return redirect('helper:dashboard_student')

        # Check for required subjects
        required_subjects = {
            "Life Orientation": False,
            "Mathematics": False,
            "Mathematical Literacy": False,
            "Language": False
        }

        for subject in marks:
            if subject == "Life Orientation":
                required_subjects["Life Orientation"] = True
            elif subject in ["Mathematics", "Mathematical Literacy"]:
                required_subjects[subject] = True
            elif "Language" in subject:
                required_subjects["Language"] = True

        # Validate required subjects
        if not required_subjects["Life Orientation"]:
            messages.error(request, "Life Orientation is required.")
            return redirect('helper:dashboard_student')
        if not (required_subjects["Mathematics"] or required_subjects["Mathematical Literacy"]):
            messages.error(request, "Either Mathematics or Mathematical Literacy is required.")
            return redirect('helper:dashboard_student')
        if not required_subjects["Language"]:
            messages.error(request, "At least one language subject is required.")
            return redirect('helper:dashboard_student')

        # Calculate APS
        aps = calculate_aps(marks)
        if aps is None:
            messages.error(request, "Error calculating APS score. Please check your marks.")
            return redirect('helper:dashboard_student')

        # Update profile with marks and APS
        profile.marks = marks
        profile.stored_aps_score = aps
        profile.save()

        # Get number of qualified universities
        qualified_count = University.objects.filter(minimum_aps__lte=aps).count()
        messages.success(request, f"Marks updated successfully! Your APS score is {aps}. You qualify for {qualified_count} universities.")
        return redirect('helper:dashboard_student')
    
    # For GET requests, redirect to dashboard
    return redirect('helper:dashboard_student')

@login_required
def whatsapp_settings(request):
    """Handle WhatsApp notification settings."""
    profile = get_object_or_404(StudentProfile, user=request.user)
    if not profile.can_access_whatsapp_chat():
        messages.error(request, "WhatsApp chat is only available for Premium and Ultimate packages.")
        return redirect('helper:dashboard_student')
    
    if request.method == 'POST':
        form = WhatsAppEnableForm(request.POST)
        if form.is_valid():
            profile.whatsapp_enabled = form.cleaned_data['enable_whatsapp']
            profile.phone_number = form.cleaned_data['phone_number']
            profile.save()
            messages.success(request, "WhatsApp settings updated successfully!")
            return redirect('helper:dashboard_student')
    else:
        form = WhatsAppEnableForm(initial={
            'enable_whatsapp': profile.whatsapp_enabled,
            'phone_number': profile.phone_number
        })
    return render(request, 'helper/whatsapp_settings.html', {'form': form})

@login_required
def upload_document(request):
    """Handle document uploads, allowing only one upload per document type per user and filtering the dropdown."""
    # Get all document types
    all_types = dict(DocumentUpload.DOCUMENT_TYPES)
    # Get types already uploaded by the user
    uploaded_types = set(DocumentUpload.objects.filter(user=request.user).values_list('document_type', flat=True))
    # Only allow types not already uploaded
    available_types = [(k, v) for k, v in DocumentUpload.DOCUMENT_TYPES if k not in uploaded_types or k == 'payment_proof']

    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            document_type = form.cleaned_data['document_type']
            
            # Special handling for PoP to prevent duplicate check if we allow multiple PoPs
            if document_type != 'payment_proof':
                existing = DocumentUpload.objects.filter(user=request.user, document_type=document_type)
                if existing.exists():
                    messages.error(request, f"You have already uploaded a document for '{dict(DocumentUpload.DOCUMENT_TYPES).get(document_type, document_type)}'. Please delete it before uploading a new one.")
                    return redirect('helper:document_list')

            document = form.save(commit=False)
            document.user = request.user
            
            if document_type == 'payment_proof':
                university_id = request.POST.get('university_id')
                if university_id:
                    try:
                        university_instance = University.objects.get(id=university_id)
                        document.university = university_instance
                    except University.DoesNotExist:
                        messages.error(request, "Associated university for Proof of Payment not found.")
                        print(f"Warning: University with ID {university_id} not found for PoP upload by user {request.user.id}")
            
            document.save()
            messages.success(request, "Document uploaded successfully!")
            return redirect('helper:document_list')  # Changed from dashboard_student to document_list
    else:
        form = DocumentUploadForm()
        # Limit the dropdown to available types
        form.fields['document_type'].choices = [(k, v) for k, v in DocumentUpload.DOCUMENT_TYPES if k not in uploaded_types and k != 'payment_proof']
        
    return render(request, 'helper/upload_document.html', {'form': form})

@login_required
def document_list(request):
    """Display list of uploaded documents."""
    documents = DocumentUpload.objects.filter(user=request.user)
    return render(request, 'helper/document_list.html', {'documents': documents})

@login_required
def delete_document(request, doc_id):
    """Handle document deletion."""
    document = get_object_or_404(DocumentUpload, id=doc_id, user=request.user)
    
    # If this is a payment proof document, update the application status
    if document.document_type == 'payment_proof' and document.university:
        try:
            application = ApplicationStatus.objects.get(
                student__user=request.user,
                university=document.university
            )
            application.payment_verified = False
            application.status = 'not_started'  # Reset status to not_started
            application.save()
        except ApplicationStatus.DoesNotExist:
            pass  # Handle case where application doesn't exist
    
    document.delete()
    messages.success(request, "Document deleted successfully!")
    return redirect('helper:document_list')

@login_required
def edit_document(request, doc_id):
    """Handle document editing."""
    document = get_object_or_404(DocumentUpload, id=doc_id, user=request.user)
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            form.save()
            messages.success(request, "Document updated successfully!")
            return redirect('helper:document_list')
    else:
        form = DocumentUploadForm(instance=document)
    return render(request, 'helper/edit_document.html', {'form': form})

@login_required
def verify_document(request, doc_id):
    """Handle document verification."""
    try:
        document = get_object_or_404(DocumentUpload, id=doc_id)
        if not request.user.is_staff:
            logger.warning(f"Unauthorized document verification attempt by user {request.user.id}")
            raise PermissionDenied
        
        if request.method == 'POST':
            form = DocumentVerificationForm(request.POST)
            if form.is_valid():
                document.verified = form.cleaned_data['verified']
                document.notes = form.cleaned_data['notes']
                document.save()
                
                logger.info(f"Document {doc_id} verification status updated to {document.verified} by staff {request.user.id}")
                
                # If this is a subscription payment document, update related records
                if document.document_type == 'subscription_payment':
                    # Update any related payment records
                    updated_payments = Payment.objects.filter(
                        user=document.user,
                        payment_status='pending'
                    ).update(
                        payment_status='paid' if document.verified else 'not_paid',
                        verification_date=timezone.now() if document.verified else None
                    )
                    logger.info(f"Updated {updated_payments} payment records for user {document.user.id}")
                    
                    # Update any related application statuses
                    updated_applications = ApplicationStatus.objects.filter(
                        student__user=document.user,
                        status='pending'
                    ).update(
                        payment_verified=document.verified
                    )
                    logger.info(f"Updated {updated_applications} application statuses for user {document.user.id}")
                
                messages.success(request, "Document verification status updated!")
                return redirect('helper:document_list')
            else:
                logger.warning(f"Invalid form data for document {doc_id}: {form.errors}")
        else:
            form = DocumentVerificationForm(initial={
                'verified': document.verified,
                'notes': document.notes
            })
        return render(request, 'helper/verify_document.html', {'form': form, 'document': document})
    except Exception as e:
        logger.error(f"Error in verify_document for document {doc_id}: {str(e)}", exc_info=True)
        messages.error(request, "An error occurred while verifying the document.")
        return redirect('helper:document_list')

@login_required
def universities_list(request):
    """Display list of universities."""
    profile = get_object_or_404(StudentProfile, user=request.user)
    form = UniversitySearchForm(request.GET)
    
    # Handle POST request for updating selections
    if request.method == 'POST':
        selected_uni_ids = request.POST.getlist('universities')
        application_limit = profile.get_application_limit()

        if len(selected_uni_ids) > application_limit:
            messages.error(
                request, 
                mark_safe(f"You can only select up to {application_limit} "
                          f"universities with your current <a href='{reverse('helper:subscription_selection')}' class='alert-link'>"
                          f"{profile.get_subscription_package_display()} package</a>. "
                          f"Please upgrade your plan to select more or deselect some universities.")
            )
            return redirect('helper:universities_list')

        # Clear existing selections
        profile.selected_universities.clear()
        ApplicationStatus.objects.filter(student=profile).delete()
        
        # Add new selections
        valid_selections_count = 0
        for uni_id in selected_uni_ids:
            try:
                university = University.objects.get(id=uni_id)
                # Ensure student meets APS score requirement for the university
                if profile.stored_aps_score is not None and university.minimum_aps <= profile.stored_aps_score:
                    profile.selected_universities.add(university)
                    ApplicationStatus.objects.create(
                        student=profile,
                        university=university,
                        status='pending'
                    )
                    valid_selections_count += 1
                else:
                    # Optionally, inform user about universities they don't qualify for if selected
                    messages.warning(request, f"You do not meet the APS requirement for {university.name} and it was not added to your selections.")
            except University.DoesNotExist:
                messages.error(request, f"University with ID {uni_id} not found and was not added.")
                continue
        
        profile.application_count = valid_selections_count # Use count of successfully added universities
        profile.save()
        
        if valid_selections_count > 0:
            messages.success(request, f"Successfully updated your selections with {valid_selections_count} universities.")
        else:
            messages.warning(request, "No universities were added to your selections. This might be due to APS score requirements or if no universities were chosen.")
        return redirect('helper:universities_list')
    
    # Get student's APS score
    student_aps = profile.stored_aps_score
    
    # Get all universities
    universities = University.objects.all()
    
    # Apply search filters if form is valid
    if form.is_valid():
        if form.cleaned_data.get('search'):
            universities = universities.filter(name__icontains=form.cleaned_data['search'])
        if form.cleaned_data.get('province'):
            universities = universities.filter(province=form.cleaned_data['province'])
        if form.cleaned_data.get('min_aps'):
            universities = universities.filter(minimum_aps__lte=form.cleaned_data['min_aps'])
    
    # Get eligible universities based on APS score
    eligible_universities = []
    if student_aps:
        # Get universities that match the student's APS score
        eligible_unis = universities.filter(minimum_aps__lte=student_aps)
        
        # Convert QuerySet to list of dictionaries with additional data
        for uni in eligible_unis:
            uni_data = {
                'university': uni,
                'is_selected': uni in profile.selected_universities.all(),
                'fee': APPLICATION_FEES_2025.get(uni.name, "Not specified"),
                'due_date': UNIVERSITY_DUE_DATES.get(uni.name, "Not specified")
            }
            eligible_universities.append(uni_data)
    
    # Get selected universities with details
    selected_with_details = []
    for uni in profile.selected_universities.all():
        uni_data = {
            'university': uni,
            'application_fee': APPLICATION_FEES_2025.get(uni.name, "Not specified"),
            'due_date': UNIVERSITY_DUE_DATES.get(uni.name, "Not specified"),
            'faculties_open': FACULTIES_OPEN.get(uni.name, [])
        }
        selected_with_details.append(uni_data)
    
    # Calculate payment breakdown using shared function
    payment_breakdown, total_university_fee = calculate_application_fees(selected_with_details)
    
    # Get package cost
    package_cost = 0
    if profile.subscription_package == 'basic':
        package_cost = 400
    elif profile.subscription_package == 'standard':
        package_cost = 600
    elif profile.subscription_package == 'premium':
        package_cost = 800
    elif profile.subscription_package == 'ultimate':
        package_cost = 1000
    
    # Calculate total payment
    total_payment = total_university_fee + package_cost
    
    context = {
        'universities': universities,
        'form': form,
        'title': 'Universities',
        'student_aps': student_aps,
        'eligible_universities': eligible_universities,
        'selected_with_details': selected_with_details,
        'payment_breakdown': payment_breakdown,
        'total_university_fee': total_university_fee,
        'package_cost': package_cost,
        'total_payment': total_payment,
        'student_profile': profile
    }
    return render(request, 'helper/universities_list.html', context)

@login_required
def university_detail(request, uni_id):
    """Display university details."""
    university = get_object_or_404(University, id=uni_id)
    # Get application fee and due date
    application_fee = APPLICATION_FEES_2025.get(university.name, "Not specified")
    due_date = UNIVERSITY_DUE_DATES.get(university.name, "Not specified")
    # Get faculties
    faculties = FACULTIES_OPEN.get(university.name, [])
    
    # Get student profile for subscription check
    profile = get_object_or_404(StudentProfile, user=request.user)
    
    context = {
        'university': university,
        'application_fee': application_fee,
        'due_date': due_date,
        'faculties_open': faculties,
        'student_profile': profile
    }
    return render(request, 'helper/university_detail.html', context)

@login_required
def university_faculties(request, uni_id):
    """Display university faculties and courses."""
    university = get_object_or_404(University, id=uni_id)
    # Get faculties for this university from FACULTIES_OPEN
    faculties = FACULTIES_OPEN.get(university.name, [])
    return render(request, 'helper/university_faculties.html', {
        'university': university,
        'faculties': faculties
    })

@login_required
def select_university(request, uni_id):
    """Handle university selection via AJAX."""
    if request.method == 'POST':
        try:
            university = University.objects.get(id=uni_id)
            profile = get_object_or_404(StudentProfile, user=request.user)

            # Check if student has reached their application limit
            application_limit = profile.get_application_limit()
            # Count current selections that are not the one currently being added (if it's already selected)
            current_selection_count = profile.selected_universities.exclude(id=uni_id).count()

            if current_selection_count >= application_limit and not profile.selected_universities.filter(id=uni_id).exists():
                upgrade_url = reverse('helper:subscription_selection')
                return JsonResponse({
                    'success': False,
                    'message': f"You have reached your limit of {application_limit} selections for the "
                               f"{profile.get_subscription_package_display()} package. "
                               f"Please <a href='{upgrade_url}' class='alert-link'>upgrade your plan</a> to select more.",
                    'upgrade_url': upgrade_url
                }, status=403) # Forbidden

            # Check if student qualifies for the university (APS score)
            if profile.stored_aps_score is not None and university.minimum_aps <= profile.stored_aps_score:
                if not profile.selected_universities.filter(id=uni_id).exists():
                    profile.selected_universities.add(university)
                    profile.application_count = profile.selected_universities.count()
                    profile.save()
                    
                    ApplicationStatus.objects.get_or_create(
                        student=profile,
                        university=university,
                        defaults={'status': 'pending'}
                    )
                    message = f'Successfully selected {university.name}.'
                else:
                    # University is already selected, no change but still success
                    message = f'{university.name} is already in your selected list.'
                
                return JsonResponse({
                    'success': True,
                    'message': message,
                    'application_count': profile.application_count
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': f'Your APS score ({profile.stored_aps_score}) does not meet the minimum requirement ({university.minimum_aps}) for {university.name}.'
                })
        except University.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'University not found'}, status=404)
        except Exception as e:
            logger.error(f"Error in select_university: {str(e)}")
            return JsonResponse({'success': False, 'message': 'An unexpected error occurred. Please try again.'}, status=500)
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)

@login_required
def deselect_university(request, uni_id):
    """Handle university deselection."""
    profile = get_object_or_404(StudentProfile, user=request.user)
    university = get_object_or_404(University, id=uni_id)
    
    if university in profile.selected_universities.all():
        profile.selected_universities.remove(university)
        profile.application_count -= 1
        profile.save()
        
        ApplicationStatus.objects.filter(
            student=profile,
            university=university
        ).delete()
        
        messages.success(request, f"Successfully removed {university.name} from your selections.")
    return redirect('helper:universities_list')

@login_required
def application_list(request):
    """Display list of applications."""
    profile = get_object_or_404(StudentProfile, user=request.user)
    
    # Only get applications for selected universities
    applications = ApplicationStatus.objects.filter(
        student=profile,
        university__in=profile.selected_universities.all()
    )
    
    # Check payment proof status for each application
    for application in applications:
        payment_proof = DocumentUpload.objects.filter(
            user=request.user,
            document_type='payment_proof',
            university=application.university
        ).first()
        
        if payment_proof:
            # If payment proof exists and 24 hours have passed, mark as verified
            time_since_upload = timezone.now() - payment_proof.uploaded_at
            if time_since_upload.total_seconds() >= 24 * 3600:  # 24 hours in seconds
                application.payment_verified = True
                application.save()
        else:
            # If no payment proof exists, ensure status is not_started
            if application.status != 'not_started':
                application.status = 'not_started'
                application.payment_verified = False
                application.save()
    
    # Prepare data for fee calculation
    universities_data = []
    for application in applications:
        fee = APPLICATION_FEES_2025.get(application.university.name, "0")
        universities_data.append({
            'university': application.university,
            'application_fee': fee
        })
    
    # Calculate payment breakdown using shared function
    payment_breakdown, total_university_fee = calculate_application_fees(universities_data)
    
    # Calculate subscription package cost
    package_cost = 0
    if profile.subscription_package == 'basic':
        package_cost = 400
    elif profile.subscription_package == 'standard':
        package_cost = 600
    elif profile.subscription_package == 'premium':
        package_cost = 800
    elif profile.subscription_package == 'ultimate':
        package_cost = 1000
    
    # Calculate total payment
    total_payment = total_university_fee + package_cost
    
    context = {
        'applications': applications,
        'payment_breakdown': payment_breakdown,
        'total_university_fee': total_university_fee,
        'package_cost': package_cost,
        'total_payment': total_payment,
        'student_profile': profile,
        'application_fees': APPLICATION_FEES_2025
    }
    return render(request, 'helper/application_list.html', context)

@login_required
def application_detail(request, app_id):
    """Display application details."""
    profile = get_object_or_404(StudentProfile, user=request.user)
    application = get_object_or_404(ApplicationStatus, id=app_id, student=profile)
    
    # Get payment proof document
    payment_proof = DocumentUpload.objects.filter(
        user=request.user,
        document_type='payment_proof',
        university=application.university
    ).first()
    
    # Check if payment proof exists and 24 hours have passed
    if payment_proof:
        time_since_upload = timezone.now() - payment_proof.uploaded_at
        if time_since_upload.total_seconds() >= 24 * 3600:  # 24 hours in seconds
            application.payment_verified = True
            application.save()
    
    context = {
        'application': application,
        'payment_proof': payment_proof,
        'time_since_upload': time_since_upload if payment_proof else None
    }
    return render(request, 'helper/application_detail.html', context)

@login_required
def update_application_status(request, app_id):
    """Handle application status updates."""
    if not request.user.is_staff:
        raise PermissionDenied
    
    application = get_object_or_404(ApplicationStatus, id=app_id)
    if request.method == 'POST':
        form = ApplicationStatusForm(request.POST)
        if form.is_valid():
            application.status = form.cleaned_data['status']
            application.tracking_number = form.cleaned_data['tracking_number']
            application.notes = form.cleaned_data['notes']
            application.save()
            messages.success(request, "Application status updated successfully!")
            return redirect('helper:application_detail', app_id=app_id)
    else:
        form = ApplicationStatusForm(initial={
            'status': application.status,
            'tracking_number': application.tracking_number,
            'notes': application.notes
        })
    return render(request, 'helper/update_application_status.html', {'form': form, 'application': application})

@login_required
def pay_application_fee(request, uni_id):
    """Handle application fee payment."""
    try:
        profile = get_object_or_404(StudentProfile, user=request.user)
        university = get_object_or_404(University, id=uni_id)
        
        # Get application fee from the dictionary
        application_fee = APPLICATION_FEES_2025.get(university.name, "Not specified")
        
        # Check if subscription payment is verified
        subscription_payment = DocumentUpload.objects.filter(
            user=request.user,
            document_type='subscription_payment',
            verified=True
        ).first()
        
        if not subscription_payment:
            messages.error(request, "Please pay and verify your subscription fee before applying to universities.")
            return redirect('helper:pay_subscription_fee')
        
        # Get or create ApplicationStatus
        application, created = ApplicationStatus.objects.get_or_create(
            student=profile,
            university=university,
            defaults={
                'status': 'not_started',
                'payment_verified': False
            }
        )
        
        # If university application is free, only require subscription payment
        if application_fee == "FREE":
            application.status = 'pending'
            application.payment_verified = True  # Auto-verify since no application fee
            application.save()
            messages.success(request, f"Application to {university.name} has been initiated. No application fee required.")
            return redirect('helper:application_detail', app_id=application.id)
        
        if request.method == 'POST':
            if request.FILES.get('payment_proof'):
                # Create the document upload
                payment_proof = DocumentUpload.objects.create(
                    user=request.user,
                    document_type='payment_proof',
                    file=request.FILES['payment_proof'],
                    university=university
                )
                
                # Update application status
                application.status = 'pending'
                application.payment_verified = False
                application.save()
                
                messages.success(request, "Payment proof uploaded successfully! Your payment will be verified within 24 hours.")
                return redirect('helper:application_detail', app_id=application.id)
            else:
                messages.error(request, "Please upload a proof of payment.")
        
        # Bank details
        bank_details = {
            'bank_name': 'Standard Bank',
            'account_holder': 'Varsity Plug',
            'account_number': '1234567890',
            'branch_code': '051001',
            'reference': f'VP-{profile.user.username}-{int(time.time())}'
        }
        
        # Calculate total payment (only subscription fee for free universities)
        total_payment = profile.get_subscription_fee()
        
        return render(request, 'helper/pay_application_fee.html', {
            'university': university,
            'application': application,
            'application_fee': application_fee,
            'bank_details': bank_details,
            'student_profile': profile,
            'total_payment': f'R{total_payment}',
            'is_free_university': application_fee == "FREE"
        })
        
    except University.DoesNotExist:
        messages.error(request, "The selected university does not exist.")
        return redirect('helper:universities_list')
    except Exception as e:
        logger.error(f"Error in pay_application_fee: {str(e)}")
        messages.error(request, "An error occurred while processing your payment request.")
        return redirect('helper:universities_list')

@login_required
def pay_application_fee_instructions(request, uni_id):
    """Display application fee payment instructions."""
    university = get_object_or_404(University, id=uni_id)
    return render(request, 'helper/payment_instructions.html', {'university': university})

@login_required
def pay_all_application_fees(request):
    """Handle payment for all application fees at once."""
    profile = get_object_or_404(StudentProfile, user=request.user)
    
    # Get all applications for selected universities
    applications = ApplicationStatus.objects.filter(
        student=profile,
        university__in=profile.selected_universities.all()
    )
    
    # Separate applications into pending and paid
    pending_applications = []
    paid_applications = []
    
    for application in applications:
        # Check for payment proof using DocumentUpload model
        payment_proof = DocumentUpload.objects.filter(
            user=request.user,
            document_type='payment_proof',
            university=application.university
        ).first()
        
        if payment_proof and payment_proof.verified:
            paid_applications.append(application)
        else:
            pending_applications.append(application)
    
    # Prepare data for fee calculation
    universities_data = []
    for application in applications:
        universities_data.append({
            'university': application.university,
            'application_fee': APPLICATION_FEES_2025.get(application.university.name, "0")
        })
    
    # Calculate payment breakdown using shared function
    payment_breakdown, total_university_fee = calculate_application_fees(universities_data)
    
    # Calculate subscription package cost
    package_cost = 0
    if profile.subscription_package == 'basic':
        package_cost = 400
    elif profile.subscription_package == 'standard':
        package_cost = 600
    elif profile.subscription_package == 'premium':
        package_cost = 800
    elif profile.subscription_package == 'ultimate':
        package_cost = 1000
    
    # Calculate total payment (university fees + subscription)
    total_payment = total_university_fee + package_cost
    
    # Bank details
    bank_details = {
        'bank_name': 'Standard Bank',
        'account_holder': 'Varsity Plug',
        'account_number': '1234567890',
        'branch_code': '051001',
        'reference': f'VP-{profile.user.username}-{int(time.time())}'
    }
    
    if request.method == 'POST':
        if request.FILES.get('payment_proof'):
            reference_number = request.POST.get('reference_number')
            if not reference_number:
                messages.error(request, "Please provide a payment reference number.")
                return redirect('helper:pay_all_application_fees')
            
            # Create a document upload for each pending application
            for application in pending_applications:
                DocumentUpload.objects.create(
                    user=request.user,
                    document_type='payment_proof',
                    file=request.FILES['payment_proof'],
                    university=application.university,
                    reference_number=reference_number
                )
                application.payment_verified = False  # Will be verified by admin
                application.save()
            
            messages.success(request, "Payment proof uploaded successfully! Your payment will be verified within 24 hours.")
            return redirect('helper:application_list')
    
    context = {
        'applications': applications,
        'pending_applications': pending_applications,
        'paid_applications': paid_applications,
        'payment_breakdown': payment_breakdown,
        'total_university_fee': total_university_fee,
        'package_cost': package_cost,
        'total_payment': total_payment,
        'bank_details': bank_details,
        'student_profile': profile
    }
    
    return render(request, 'helper/pay_all_fees.html', context)

@login_required
@ratelimit(key='user', rate='10/m', block=True)
def ai_chat(request):
    """Handle AI chat interactions via POST AJAX requests."""
    # Ensure this view is only accessed via POST by AJAX
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    try:
        # Get user's profile and check subscription
        profile = get_object_or_404(StudentProfile, user=request.user)
        if not profile.subscription_status:
            subscription_url = reverse('helper:pay_subscription_fee')
            return JsonResponse({
                'error': f'Please update your subscription to use the AI chat feature. <a href="{subscription_url}" class="alert-link">Click here to update your subscription</a>.'
            }, status=403)

        # The frontend sends JSON, so parse request.body
        payload = json.loads(request.body)
        message = payload.get('message')

        if not message or not isinstance(message, str) or not message.strip():
            return JsonResponse({'error': 'Message is required and must be a non-empty string.'}, status=400)

    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body")
        return JsonResponse({'error': 'Invalid JSON format in request body.'}, status=400)
    except Exception as e:
        logger.error(f"Error processing chat request payload: {str(e)}", exc_info=True)
        return JsonResponse({'error': 'Error processing your request data.'}, status=400)

    try:
        # Check if OpenAI API key is configured
        if not hasattr(settings, 'OPENAI_API_KEY'):
            logger.critical("OPENAI_API_KEY not found in settings")
            return JsonResponse({'error': "AI service not configured."}, status=503)
        
        if not settings.OPENAI_API_KEY:
            logger.critical("OPENAI_API_KEY is empty in settings")
            return JsonResponse({'error': "AI service not configured."}, status=503)

        # Ensure openai is imported and api_key is set
        if openai.api_key is None:
            logger.info("Setting OpenAI API key from settings")
            openai.api_key = settings.OPENAI_API_KEY

        # Use the latest OpenAI API format
        try:
            logger.info("Initializing OpenAI client")
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            
            logger.info("Sending request to OpenAI API")
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful university application assistant."},
                    {"role": "user", "content": message.strip()}
                ]
            )
            ai_response = response.choices[0].message.content
            logger.info("Successfully received response from OpenAI")
            
            return JsonResponse({'response': ai_response})
        except Exception as api_error:
            logger.error(f"Error during OpenAI API call: {str(api_error)}", exc_info=True)
            raise

    except openai.OpenAIError as e:
        logger.error(f"OpenAI API Error: {str(e)}", exc_info=True)
        return JsonResponse({'error': f"OpenAI Error: {str(e)}"}, status=502)
    except Exception as e:
        logger.error(f"AI chat interaction error (Other): {str(e)}", exc_info=True)
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error details: {str(e)}")
        return JsonResponse({'error': "I'm sorry, but an internal error occurred while processing your chat message."}, status=500)

@login_required
def chat_history(request):
    """Display chat history."""
    # This would typically integrate with a chat history model
    return render(request, 'helper/chat_history.html')

@login_required
def course_advice(request):
    """Display course advice."""
    profile = get_object_or_404(StudentProfile, user=request.user)
    if not profile.can_access_course_advice():
        messages.error(request, "Course advice is only available for Premium and Ultimate packages.")
        return redirect('helper:dashboard_student')
    return render(request, 'helper/course_advice.html')

@login_required
def university_course_advice(request, uni_id):
    """Display university-specific course advice."""
    profile = get_object_or_404(StudentProfile, user=request.user)
    if not profile.can_access_course_advice():
        messages.error(request, "Course advice is only available for Premium and Ultimate packages.")
        return redirect('helper:dashboard_student')
    
    university = get_object_or_404(University, id=uni_id)
    return render(request, 'helper/university_course_advice.html', {'university': university})

@login_required
def fee_guidance(request):
    """Display fee guidance."""
    profile = get_object_or_404(StudentProfile, user=request.user)
    if not profile.can_access_fee_guidance():
        messages.error(request, "Fee guidance is only available for Standard, Premium, and Ultimate packages.")
        return redirect('helper:dashboard_student')
    return render(request, 'helper/fee_guidance.html')

@login_required
def university_fee_guidance(request, uni_id):
    """Display university-specific fee guidance."""
    profile = get_object_or_404(StudentProfile, user=request.user)
    if not profile.can_access_fee_guidance():
        messages.error(request, "Fee guidance is only available for Standard, Premium, and Ultimate packages.")
        return redirect('helper:dashboard_student')
    
    university = get_object_or_404(University, id=uni_id)
    return render(request, 'helper/university_fee_guidance.html', {'university': university})

@login_required
def concierge_service(request):
    """Display concierge service."""
    profile = get_object_or_404(StudentProfile, user=request.user)
    if not profile.can_access_concierge_service():
        messages.error(request, "Concierge service is only available for Ultimate package subscribers.")
        return redirect('helper:dashboard_student')
    return render(request, 'helper/concierge_service.html')

@login_required
def concierge_request(request):
    """Handle concierge service requests."""
    profile = get_object_or_404(StudentProfile, user=request.user)
    if not profile.can_access_concierge_service():
        messages.error(request, "Concierge service is only available for Ultimate package subscribers.")
        return redirect('helper:dashboard_student')
    
    if request.method == 'POST':
        # Process concierge request
        messages.success(request, "Your concierge request has been submitted!")
        return redirect('helper:dashboard_student')
    
    return render(request, 'helper/concierge_request.html')

@login_required
def university_search_api(request):
    """API endpoint for university search."""
    query = request.GET.get('q', '')
    universities = University.objects.filter(name__icontains=query)
    data = [{'id': u.id, 'name': u.name, 'province': u.province} for u in universities]
    return JsonResponse({'universities': data})

@login_required
def verify_document_api(request):
    """API endpoint for document verification."""
    if not request.user.is_staff:
        logger.warning(f"Unauthorized document verification attempt by user {request.user.id}")
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    if request.method == 'POST':
        try:
            doc_id = request.POST.get('doc_id')
            verified = request.POST.get('verified') == 'true'
            notes = request.POST.get('notes', '')
            
            document = DocumentUpload.objects.get(id=doc_id)
            document.verified = verified
            document.notes = notes
            document.save()
            
            logger.info(f"Document {doc_id} verification status updated to {verified} by staff {request.user.id}")
            
            # If this is a subscription payment document, update related records
            if document.document_type == 'subscription_payment':
                # Update any related payment records
                updated_payments = Payment.objects.filter(
                    user=document.user,
                    payment_status='pending'
                ).update(
                    payment_status='paid' if document.verified else 'not_paid',
                    verification_date=timezone.now() if document.verified else None
                )
                logger.info(f"Updated {updated_payments} payment records for user {document.user.id}")
                
                # Update any related application statuses
                updated_applications = ApplicationStatus.objects.filter(
                    student__user=document.user,
                    status='pending'
                ).update(
                    payment_verified=document.verified
                )
                logger.info(f"Updated {updated_applications} application statuses for user {document.user.id}")
            
            return JsonResponse({
                'status': 'success',
                'message': 'Document verification status updated successfully'
            })
        except DocumentUpload.DoesNotExist:
            logger.error(f"Document {doc_id} not found")
            return JsonResponse({'error': 'Document not found'}, status=404)
        except Exception as e:
            logger.error(f"Error verifying document {doc_id}: {str(e)}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)
    
    logger.warning(f"Invalid request method {request.method} for document verification")
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def edit_marks(request):
    """Handle editing of student marks and subjects."""
    profile = get_object_or_404(StudentProfile, user=request.user)
    
    if request.method == 'POST':
        # Get all subject and mark pairs from the form
        marks = {}
        for i in range(7):
            subject = request.POST.get(f'subject_{i}')
            mark = request.POST.get(f'mark_{i}')
            if subject and mark:
                try:
                    mark = int(mark)
                    if 0 <= mark <= 100:
                        marks[subject] = mark
                except (ValueError, TypeError):
                    continue

        # Validate marks
        if len(marks) != 7:
            messages.error(request, "Please enter exactly 7 subject marks.")
            return redirect('helper:edit_marks')

        # Check for required subjects
        required_subjects = {
            "Life Orientation": False,
            "Mathematics": False,
            "Mathematical Literacy": False,
            "Language": False
        }

        for subject in marks:
            if subject == "Life Orientation":
                required_subjects["Life Orientation"] = True
            elif subject in ["Mathematics", "Mathematical Literacy"]:
                required_subjects[subject] = True
            elif "Language" in subject:
                required_subjects["Language"] = True

        # Validate required subjects
        if not required_subjects["Life Orientation"]:
            messages.error(request, "Life Orientation is required.")
            return redirect('helper:edit_marks')
        if not (required_subjects["Mathematics"] or required_subjects["Mathematical Literacy"]):
            messages.error(request, "Either Mathematics or Mathematical Literacy is required.")
            return redirect('helper:edit_marks')
        if not required_subjects["Language"]:
            messages.error(request, "At least one language subject is required.")
            return redirect('helper:edit_marks')

        # Calculate APS
        aps = calculate_aps(marks)
        if aps is None:
            messages.error(request, "Error calculating APS score. Please check your marks.")
            return redirect('helper:edit_marks')

        # Update profile with marks and APS
        profile.marks = marks
        profile.stored_aps_score = aps
        profile.save()

        # Get number of qualified universities
        qualified_count = University.objects.filter(minimum_aps__lte=aps).count()
        messages.success(request, f"Marks updated successfully! Your APS score is {aps}. You qualify for {qualified_count} universities.")
        return redirect('helper:edit_marks')
    
    # Prepare marks list for the template
    marks_list = []
    if profile.marks:
        for subject, mark in profile.marks.items():
            marks_list.append({
                'subject': subject,
                'mark': mark
            })
    else:
        marks_list = [{'subject': None, 'mark': None} for _ in range(7)]
    
    context = {
        'profile': profile,
        'marks_list': marks_list,
        'nsc_subjects': NSC_SUBJECTS,
        'student_aps': profile.stored_aps_score,
        'title': 'Edit Marks'
    }
    return render(request, 'helper/edit_marks.html', context)

@login_required
def universities_api(request):
    """API endpoint for university slideshow data."""
    profile = get_object_or_404(StudentProfile, user=request.user)
    
    # Get universities that match the student's APS score
    universities = University.objects.filter(
        minimum_aps__lte=profile.stored_aps_score
    ).order_by('minimum_aps')
    
    # Convert QuerySet to list of dictionaries with additional data
    universities_data = []
    for uni in universities:
        uni_data = {
            'id': uni.id,
            'name': uni.name,
            'province': uni.province,
            'minimum_aps': uni.minimum_aps,
            'due_date': UNIVERSITY_DUE_DATES.get(uni.name, "Not specified"),
            'application_fee': APPLICATION_FEES_2025.get(uni.name, "Not available"),
            'detail_url': reverse('helper:university_detail', args=[uni.id]),
            'select_url': reverse('helper:select_university', args=[uni.id])
        }
        universities_data.append(uni_data)
    
    return JsonResponse({'universities': universities_data})

@login_required
def view_payment_proof(request, app_id):
    """View payment proof for an application."""
    try:
        profile = get_object_or_404(StudentProfile, user=request.user)
        application = get_object_or_404(ApplicationStatus, id=app_id, student=profile)
        
        # Get the payment proof document
        payment_proof = DocumentUpload.objects.filter(
            user=request.user,
            document_type='payment_proof',
            university=application.university
        ).first()
        
        if not payment_proof:
            messages.error(request, "No payment proof found for this application.")
            return redirect('helper:application_list')
        
        # Check if the file is a PDF
        is_pdf = payment_proof.file.url.lower().endswith('.pdf')
        
        context = {
            'payment_proof': payment_proof,
            'application': application,
            'is_pdf': is_pdf,
            'university_name': application.university.name,
            'upload_date': payment_proof.uploaded_at,
            'verification_status': 'Verified' if payment_proof.verified else 'Pending Verification',
            'verification_date': payment_proof.verification_date if payment_proof.verified else None
        }
        
        return render(request, 'helper/view_payment_proof.html', context)
        
    except ApplicationStatus.DoesNotExist:
        messages.error(request, "Application not found.")
        return redirect('helper:application_list')
    except Exception as e:
        logger.error(f"Error viewing payment proof: {str(e)}")
        messages.error(request, "An error occurred while viewing the payment proof.")
        return redirect('helper:application_list')

@login_required
def pay_subscription_fee(request):
    """Handle subscription fee payment."""
    profile = get_object_or_404(StudentProfile, user=request.user)
    
    # Check for existing subscription payment
    existing_payment = DocumentUpload.objects.filter(
        user=request.user,
        document_type='subscription_payment'
    ).first()
    
    # Get subscription status for display
    subscription_status = "Not Paid"
    if existing_payment:
        time_since_upload = timezone.now() - existing_payment.uploaded_at
        if time_since_upload.total_seconds() >= 24 * 3600:  # 24 hours in seconds
            subscription_status = "Verified"
        else:
            subscription_status = "Pending Verification"
            minutes_ago = int(time_since_upload.total_seconds() / 60)
            subscription_status += f" (Uploaded {minutes_ago} minutes ago)"
    
    if request.method == 'POST':
        if existing_payment:
            messages.error(request, "You have already uploaded a subscription payment proof. Please wait for verification.")
            return redirect('helper:dashboard_student')
            
        if request.FILES.get('payment_proof'):
            # Create the document upload for subscription payment
            payment_proof = DocumentUpload.objects.create(
                user=request.user,
                document_type='subscription_payment',
                file=request.FILES['payment_proof']
            )
            
            messages.success(request, "Subscription payment proof uploaded successfully! Your payment will be verified within 24 hours.")
            return redirect('helper:dashboard_student')
        else:
            messages.error(request, "Please upload a proof of payment.")
    
    # Bank details
    bank_details = {
        'bank_name': 'Standard Bank',
        'account_holder': 'Varsity Plug',
        'account_number': '1234567890',
        'branch_code': '051001',
        'reference': f'VP-SUB-{profile.user.username}-{int(time.time())}'
    }
    
    # Calculate subscription package cost
    package_cost = 0
    if profile.subscription_package == 'basic':
        package_cost = 400
    elif profile.subscription_package == 'standard':
        package_cost = 600
    elif profile.subscription_package == 'premium':
        package_cost = 800
    elif profile.subscription_package == 'ultimate':
        package_cost = 1000
    
    return render(request, 'helper/pay_subscription_fee.html', {
        'student_profile': profile,
        'bank_details': bank_details,
        'subscription_status': subscription_status,
        'existing_payment': existing_payment,
        'package_cost': package_cost
    })

@login_required
def upgrade_subscription(request):
    """Handle subscription upgrades."""
    profile = get_object_or_404(StudentProfile, user=request.user)
    
    # Define package details
    packages = {
        'basic': {
            'name': 'Basic Package',
            'price': 400,
            'includes': 'Access to university applications, Basic application tracking, Email support'
        },
        'standard': {
            'name': 'Standard Package',
            'price': 600,
            'includes': 'All Basic features, Priority application processing, Document verification, 24/7 support'
        },
        'premium': {
            'name': 'Premium Package',
            'price': 800,
            'includes': 'All Standard features, Personal application advisor, Expedited processing, Priority support, Application review'
        },
        'ultimate': {
            'name': 'Ultimate Package',
            'price': 1000,
            'includes': 'All Premium features, Unlimited applications, Concierge service, 24/7 priority support'
        }
    }
    
    # Get available upgrades based on current package
    package_order = ['basic', 'standard', 'premium', 'ultimate']
    current_index = package_order.index(profile.subscription_package)
    available_upgrades = {
        pkg: details for pkg, details in packages.items()
        if package_order.index(pkg) > current_index
    }
    
    if request.method == 'POST':
        new_package = request.POST.get('new_package')
        if new_package in available_upgrades:
            upgrade_cost = packages[new_package]['price'] - packages[profile.subscription_package]['price']
            if request.FILES.get('payment_proof'):
                # Create document upload for upgrade payment
                DocumentUpload.objects.create(
                    user=request.user,
                    document_type='subscription_payment',
                    file=request.FILES['payment_proof']
                )
                profile.subscription_package = new_package
                profile.save()
                messages.success(request, f"Upgrade to {packages[new_package]['name']} submitted! Your payment will be verified within 24 hours.")
                return redirect('helper:dashboard_student')
            else:
                messages.error(request, "Please upload proof of payment for the upgrade.")
    
    # Prepare context for template
    context = {
        'student_profile': profile,
        'available_upgrades': available_upgrades,
        'packages': packages,
        'current_package': packages[profile.subscription_package],
        'is_upgrade': True
    }
    
    return render(request, 'helper/upgrade_subscription.html', context)

@login_required
def unified_payment(request):
    """Handle all types of payments in one place."""
    profile = get_object_or_404(StudentProfile, user=request.user)
    
    # Get all applications for selected universities
    applications = ApplicationStatus.objects.filter(
        student=profile,
        university__in=profile.selected_universities.all()
    )
    
    # Get all payments and documents
    payments = Payment.objects.filter(user=request.user)
    documents = DocumentUpload.objects.filter(
        user=request.user,
        document_type__in=['payment_proof', 'subscription_payment']
    )
    
    # Check subscription payment status
    subscription_payment = DocumentUpload.objects.filter(
        user=request.user,
        document_type='subscription_payment'
    ).first()
    
    # Get subscription status for display
    subscription_status = "Not Paid"
    if subscription_payment:
        time_since_upload = timezone.now() - subscription_payment.uploaded_at
        if time_since_upload.total_seconds() >= 24 * 3600:  # 24 hours in seconds
            subscription_status = "Verified"
        else:
            subscription_status = "Pending Verification"
            minutes_ago = int(time_since_upload.total_seconds() / 60)
            subscription_status += f" (Uploaded {minutes_ago} minutes ago)"
    
    # Update payment statuses based on document verification
    for application in applications:
        # Check for payment proof document
        payment_proof = DocumentUpload.objects.filter(
            user=request.user,
            document_type='payment_proof',
            university=application.university
        ).first()
        
        # Get application fee and parse it
        application_fee = APPLICATION_FEES_2025.get(application.university.name, "0")
        if application_fee == "FREE":
            amount = 0
            # For free applications, automatically mark as paid
            application.payment_verified = True
            application.status = 'pending'
            application.save()
            
            # Update or create payment record for free applications
            payment, created = Payment.objects.get_or_create(
                user=request.user,
                university=application.university.name,
                defaults={
                    'payment_status': 'paid',
                    'amount': 0
                }
            )
            if not created:
                payment.payment_status = 'paid'
                payment.amount = 0
                payment.save()
        else:
            # Handle different fee formats
            try:
                # Remove 'R' and spaces
                fee_str = application_fee.replace('R', '').replace(' ', '')
                # If there are multiple fees (e.g., "250(on-time),470(late)")
                if ',' in fee_str:
                    # Take the first fee (on-time fee)
                    amount = int(fee_str.split(',')[0].split('(')[0])
                else:
                    # Single fee
                    amount = int(fee_str.split('(')[0])
            except (ValueError, IndexError):
                # If parsing fails, default to 0
                amount = 0
        
            # Get or create payment record for paid applications
            payment, created = Payment.objects.get_or_create(
                user=request.user,
                university=application.university.name,
                defaults={
                    'payment_status': 'not_paid',
                    'amount': amount
                }
            )
            
            if payment_proof:
                # If payment proof exists and 24 hours have passed, mark as verified
                time_since_upload = timezone.now() - payment_proof.uploaded_at
                if time_since_upload.total_seconds() >= 24 * 3600:  # 24 hours in seconds
                    application.payment_verified = True
                    application.status = 'pending'
                    payment.payment_status = 'paid'
                else:
                    # If document is not verified, set status to pending
                    application.payment_verified = False
                    application.status = 'pending'
                    payment.payment_status = 'pending'
                
                application.save()
                payment.save()
            else:
                # If no payment proof exists, ensure status is not_started
                if application.status != 'not_started':
                    application.status = 'not_started'
                    application.payment_verified = False
                    application.save()
                
                # Update payment status to not_paid
                payment.payment_status = 'not_paid'
                payment.save()
    
    # Handle payment proof upload
    if request.method == 'POST':
        if request.FILES.get('payment_proof'):
            university = request.POST.get('university')
            proof_file = request.FILES['payment_proof']
            reference_number = request.POST.get('reference_number')
            
            if university and proof_file:
                try:
                    university_instance = University.objects.get(name=university)
                    
                    # Get application fee and parse it
                    application_fee = APPLICATION_FEES_2025.get(university, "0")
                    if application_fee == "FREE":
                        messages.warning(request, 'No payment proof required for free applications.')
                        return redirect('helper:unified_payment')
                    
                    # Handle different fee formats
                    try:
                        # Remove 'R' and spaces
                        fee_str = application_fee.replace('R', '').replace(' ', '')
                        # If there are multiple fees (e.g., "250(on-time),470(late)")
                        if ',' in fee_str:
                            # Take the first fee (on-time fee)
                            amount = int(fee_str.split(',')[0].split('(')[0])
                        else:
                            # Single fee
                            amount = int(fee_str.split('(')[0])
                    except (ValueError, IndexError):
                        # If parsing fails, default to 0
                        amount = 0
                    
                    # Create or update payment record
                    payment, created = Payment.objects.get_or_create(
                        user=request.user,
                        university=university,
                        defaults={
                            'payment_status': 'pending',
                            'proof_of_payment': proof_file,
                            'amount': amount
                        }
                    )
                    
                    if not created:
                        payment.payment_status = 'pending'
                        payment.proof_of_payment = proof_file
                        payment.save()
                    
                    # Create document upload record
                    document = DocumentUpload.objects.create(
                        user=request.user,
                        document_type='payment_proof',
                        file=proof_file,
                        university=university_instance
                    )
                    
                    # Update application status
                    try:
                        application = ApplicationStatus.objects.get(
                            student__user=request.user,
                            university=university_instance
                        )
                        application.status = 'pending'
                        application.payment_verified = False
                        application.save()
                        
                        messages.success(request, 'Payment proof uploaded successfully. Awaiting verification.')
                    except ApplicationStatus.DoesNotExist:
                        messages.warning(request, 'Application record not found for this university.')
                    
                except University.DoesNotExist:
                    messages.error(request, 'Invalid university selected.')
    
    # Calculate total amounts
    total_application_fees = 0
    for app in applications:
        fee = APPLICATION_FEES_2025.get(app.university.name, "0")
        if fee != "FREE":
            try:
                # Remove 'R' and spaces
                fee_str = fee.replace('R', '').replace(' ', '')
                # If there are multiple fees (e.g., "250(on-time),470(late)")
                if ',' in fee_str:
                    # Take the first fee (on-time fee)
                    amount = int(fee_str.split(',')[0].split('(')[0])
                else:
                    # Single fee
                    amount = int(fee_str.split('(')[0])
                total_application_fees += amount
            except (ValueError, IndexError):
                continue
    
    # Get subscription fee
    subscription_fee = profile.get_subscription_fee()
    
    context = {
        'profile': profile,
        'applications': applications,
        'payments': payments,
        'documents': documents,
        'subscription_payment': subscription_payment,
        'subscription_status': subscription_status,
        'total_application_fees': total_application_fees,
        'subscription_fee': subscription_fee,
        'total_amount': total_application_fees + subscription_fee,
        'application_fees': APPLICATION_FEES_2025  # Pass the dictionary to the template
    }
    
    return render(request, 'helper/unified_payment.html', context)

@login_required
def upload_payment_proof(request):
    if request.method == 'POST':
        university = request.POST.get('university')
        proof_file = request.FILES.get('proof_of_payment')
        
        if university and proof_file:
            try:
                # Get the university instance
                university_instance = University.objects.get(name=university)
                
                # Create or update payment record
                payment, created = Payment.objects.get_or_create(
                    user=request.user,
                    university=university,
                    defaults={
                        'payment_status': 'pending',
                        'proof_of_payment': proof_file
                    }
                )
                
                if not created:
                    payment.payment_status = 'pending'
                    payment.proof_of_payment = proof_file
                    payment.save()
                
                # Create document upload record
                document = DocumentUpload.objects.create(
                    user=request.user,
                    document_type='payment_proof',
                    file=proof_file,
                    university=university_instance
                )
                
                # Update application status if it exists
                try:
                    application = ApplicationStatus.objects.get(
                        student__user=request.user,
                        university=university_instance
                    )
                    application.status = 'pending'
                    application.payment_verified = False  # Will be verified by admin
                    application.save()
                    
                    messages.success(request, 'Payment proof uploaded successfully. Awaiting verification.')
                except ApplicationStatus.DoesNotExist:
                    messages.warning(request, 'Application record not found for this university.')
                
                return redirect('helper:payments')
            except University.DoesNotExist:
                messages.error(request, 'Invalid university selected.')
                return redirect('helper:payments')
    
    return render(request, 'helper/payments.html')

@login_required
def payments(request):
    profile = get_object_or_404(StudentProfile, user=request.user)
    applications = ApplicationStatus.objects.filter(student=profile)
    payments = Payment.objects.filter(user=request.user)
    documents = DocumentUpload.objects.filter(
        user=request.user,
        document_type='payment_proof'
    )
    
    # Update payment statuses based on document verification
    for application in applications:
        # Check for payment proof document
        payment_proof = DocumentUpload.objects.filter(
            user=request.user,
            document_type='payment_proof',
            university=application.university
        ).first()
        
        # Get or create payment record
        payment, created = Payment.objects.get_or_create(
            user=request.user,
            university=application.university.name,
            defaults={'payment_status': 'not_paid'}
        )
        
        if payment_proof:
            if payment_proof.verified:
                # If document is verified, update both application and payment status
                application.payment_verified = True
                application.status = 'pending'
                payment.payment_status = 'paid'
            else:
                # If document is not verified, set status to pending
                application.payment_verified = False
                application.status = 'pending'
                payment.payment_status = 'pending'
            
            application.save()
            payment.save()
        else:
            # If no payment proof exists, ensure status is not_started
            if application.status != 'not_started':
                application.status = 'not_started'
                application.payment_verified = False
                application.save()
            
            # Update payment status to not_paid
            payment.payment_status = 'not_paid'
            payment.save()
    
    context = {
        'applications': applications,
        'payments': payments,
        'documents': documents,
        'student_profile': profile
    }
    return render(request, 'helper/payments.html', context)

@login_required
@ratelimit(key='user', rate='10/m', method=['POST'])
def chat_message_api(request):
    """Handle chat message API requests."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        
        if not message:
            return JsonResponse({'error': 'Message is required'}, status=400)
        
        # Get user's profile
        profile = request.user.studentprofile
        
        # Check if user has access to chat
        if not profile.can_access_whatsapp_chat():
            return JsonResponse({
                'error': 'You need a Premium or Ultimate subscription to access the chat feature'
            }, status=403)
        
        # Process the message with OpenAI
        try:
            # Check if OpenAI API key is configured
            if not hasattr(settings, 'OPENAI_API_KEY') or not settings.OPENAI_API_KEY:
                logger.critical("OpenAI API Key not configured.")
                return JsonResponse({'error': "AI service not configured."}, status=503)

            # Use the latest OpenAI API format
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful university application assistant."},
                    {"role": "user", "content": message}
                ]
            )
            ai_response = response.choices[0].message.content
            
            # Update last chat date
            profile.last_chat_date = timezone.now()
            profile.save()
            
            return JsonResponse({
                'response': ai_response,
                'timestamp': timezone.now().isoformat()
            })
            
        except openai.OpenAIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return JsonResponse({
                'error': 'Unable to process your message at this time. Please try again later.'
            }, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Chat API error: {str(e)}")
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)