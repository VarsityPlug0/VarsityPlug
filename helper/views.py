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
    ApplicationStatusForm, DocumentVerificationForm, WhatsAppEnableForm
)
from .university_static_data import get_all_universities, get_university_by_id
import time
from .utils import calculate_application_fees
from django.db import transaction

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

def calculate_aps(marks):
    """
    Calculate APS score based on NSC marks according to official South African requirements.
    APS is calculated using the best 6 subjects (excluding Life Orientation).
    Points are awarded as follows:
    80-100% = 7 points
    70-79% = 6 points
    60-69% = 5 points
    50-59% = 4 points
    40-49% = 3 points
    30-39% = 2 points
    0-29% = 1 point
    """
    if not marks or not isinstance(marks, dict) or len(marks) != 7:
        return None

    # Store all valid subject marks
    subject_marks = []
    has_life_orientation = False

    for subject, mark in marks.items():
        if mark is None:
            return None

        try:
            mark_num = float(mark)
        except (ValueError, TypeError):
            return None

        if not 0 <= mark_num <= 100:
            return None

        # Track Life Orientation but don't include in APS calculation
        if subject == 'Life Orientation':
            has_life_orientation = True
            continue

        # Calculate points based on mark ranges
        if mark_num >= 80:
            points = 7
        elif mark_num >= 70:
            points = 6
        elif mark_num >= 60:
            points = 5
        elif mark_num >= 50:
            points = 4
        elif mark_num >= 40:
            points = 3
        elif mark_num >= 30:
            points = 2
        else:
            points = 1

        subject_marks.append(points)

    # Validate requirements
    if not has_life_orientation or len(subject_marks) != 6:
        return None

    # Calculate total APS (sum of best 6 subjects)
    aps = sum(subject_marks)

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
            try:
                with transaction.atomic():
                    user = form.save()
                    # Create StudentProfile with default package
                    StudentProfile.objects.create(
                        user=user,
                        subscription_package='basic'  # Set default package to basic
                    )
                    login(request, user)
                    messages.success(request, "Registration successful! Welcome to Varsity Plug.")
                    return redirect('helper:subscription_selection')
            except Exception as e:
                logger.error(f"Registration error: {str(e)}")
                messages.error(request, "An error occurred during registration. Please try again.")
                return render(request, 'helper/register.html', {'form': form})
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
            next_url = request.GET.get('next', 'helper:redirect_after_login')
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password. Please try again.")
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
    profile = get_object_or_404(StudentProfile, user=request.user)
    applications = ApplicationStatus.objects.filter(student=profile)
    documents = DocumentUpload.objects.filter(user=request.user)
    form = DocumentUploadForm()
    
    marks_list = []
    if profile.marks:
        for subject, mark in profile.marks.items():
            marks_list.append({'subject': subject, 'mark': mark})
    else:
        marks_list = [{'subject': None, 'mark': None} for _ in range(7)]
    
    all_static_universities = get_all_universities()
    recommended_universities_list = []
    qualified_universities_list = []
    
    # Get selected universities from profile
    selected_uni_ids = profile.selected_universities or []
    selected_universities = []
    
    # Get details for each selected university
    for uni_id in selected_uni_ids:
        uni = get_university_by_id(uni_id)
        if uni:
            uni['detail_url'] = reverse('helper:university_detail', args=[uni_id])
            selected_universities.append(uni)

    if profile.stored_aps_score is not None:
        qualified_universities_list = [
            uni for uni in all_static_universities 
            if uni['minimum_aps'] <= profile.stored_aps_score
        ]
        qualified_universities_list.sort(key=lambda x: x['minimum_aps'])
        
        recommended_universities_list = [
            uni for uni in qualified_universities_list 
            if uni['id'] not in selected_uni_ids
        ][:5]
        
        # Add detail_url and select_url to recommended_universities_list
        for uni in recommended_universities_list:
            uni['detail_url'] = reverse('helper:university_detail', args=[uni['id']])
            uni['select_url'] = reverse('helper:select_university', args=[uni['id']])

    qualified_unis_data_for_js = []
    for uni in qualified_universities_list:
        js_uni_data = uni.copy()
        js_uni_data['detail_url'] = reverse('helper:university_detail', args=[uni['id']])
        js_uni_data['select_url'] = reverse('helper:select_university', args=[uni['id']])
        qualified_unis_data_for_js.append(js_uni_data)

    context = {
        'profile': profile,
        'applications': applications,
        'documents': documents,
        'form': form,
        'title': 'Dashboard',
        'marks_list': marks_list,
        'nsc_subjects': NSC_SUBJECTS,
        'student_aps': profile.stored_aps_score,
        'recommended_universities': recommended_universities_list,
        'universities': json.dumps(qualified_unis_data_for_js, cls=DjangoJSONEncoder) if qualified_unis_data_for_js else '[]',
        'selected_universities': selected_universities,
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
    profile = get_object_or_404(StudentProfile, user=request.user)
    form = UniversitySearchForm(request.GET)
    student_aps = profile.stored_aps_score

    # Get all universities from static data
    all_universities = get_all_universities()
    universities_to_display = list(all_universities) # Start with a copy

    # Apply search filters if form is valid
    if form.is_valid():
        search_query = form.cleaned_data.get('search')
        province_filter = form.cleaned_data.get('province')
        min_aps_filter = form.cleaned_data.get('min_aps') # User's filter input for min_aps

        if search_query:
            universities_to_display = [uni for uni in universities_to_display if search_query.lower() in uni['name'].lower()]
        
        if province_filter:
            universities_to_display = [uni for uni in universities_to_display if uni['province'] == province_filter]
        
        if min_aps_filter is not None: # If user filtered by a specific APS
            universities_to_display = [uni for uni in universities_to_display if uni['minimum_aps'] <= min_aps_filter]
    
    # Prepare list for template, checking eligibility based on student's actual APS
    eligible_universities_for_template = []
    if student_aps is not None:
        for uni in universities_to_display: # Iterate through already filtered list
            aps_difference = student_aps - uni['minimum_aps']
            qualification_status = 'not_qualified'
            qualification_message = f"You are {abs(aps_difference)} points below the minimum APS requirement"

            if aps_difference >= 5:
                qualification_status = 'highly_qualified'
                qualification_message = f"You exceed the minimum APS requirement by {aps_difference} points"
            elif aps_difference >= 0:
                qualification_status = 'qualified'
                qualification_message = f"You meet the minimum APS requirement"
            
            # Add qualification data to the university dict for the template
            uni_data_for_template = uni.copy() # Work with a copy
            uni_data_for_template['qualification_status'] = qualification_status
            uni_data_for_template['qualification_message'] = qualification_message
            uni_data_for_template['aps_difference'] = aps_difference
            # Fee and due_date are already in uni dict from static_data
            # Ensure keys for template match: 'fee' might be 'application_fee' in static data
            uni_data_for_template['fee'] = uni.get('application_fee', 'N/A') 
            # 'is_selected' logic will need overhaul if University model is gone
            # For now, let's assume nothing is selected or handle it based on a list of IDs in profile
            # uni_data_for_template['is_selected'] = uni['id'] in profile.get_selected_university_ids() # Assuming such a method
            eligible_universities_for_template.append(uni_data_for_template)
    else: # If student_aps is None, show all universities from the filtered list without qualification status
        for uni in universities_to_display:
            uni_data_for_template = uni.copy()
            uni_data_for_template['qualification_status'] = 'unknown'
            uni_data_for_template['qualification_message'] = 'Your APS score is not available to determine qualification.'
            uni_data_for_template['aps_difference'] = 0
            uni_data_for_template['fee'] = uni.get('application_fee', 'N/A')
            eligible_universities_for_template.append(uni_data_for_template)

    # Sort eligible universities by qualification status and APS difference
    eligible_universities_for_template.sort(key=lambda x: (
        x['qualification_status'] == 'not_qualified', # True (1) comes after False (0)
        x['qualification_status'] == 'unknown', 
        x['qualification_status'] != 'highly_qualified', # False (0) for highly qualified first
        x['qualification_status'] != 'qualified',
        -x.get('aps_difference', 0) # Sort by largest positive difference first
    ))
    
    # Selected universities logic needs significant rework if University model is removed.
    # For now, passing an empty list or a placeholder.
    selected_with_details = [] 
    # if hasattr(profile, 'get_selected_university_details_from_static_data'):
    #    selected_with_details = profile.get_selected_university_details_from_static_data(all_universities)

    context = {
        'form': form,
        'title': 'Universities',
        'student_aps': student_aps,
        'eligible_universities': eligible_universities_for_template,
        'selected_with_details': selected_with_details, # Placeholder
        'student_profile': profile
    }
    return render(request, 'helper/universities_list.html', context)

@login_required
def university_detail(request, uni_id):
    university = get_university_by_id(uni_id)
    if not university:
        return HttpResponseNotFound("University not found.") # Or render a 404 template
    
    profile = get_object_or_404(StudentProfile, user=request.user)
    
    # Data is directly from the university dictionary
    context = {
        'university': university, # Pass the whole dictionary
        'application_fee': university.get('application_fee', "Not specified"),
        'due_date': university.get('due_date', "Not specified"),
        'faculties_open': FACULTIES_OPEN.get(university['name'], []), # Assuming FACULTIES_OPEN is still used and keyed by name
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
            profile = get_object_or_404(StudentProfile, user=request.user)
            university = get_university_by_id(uni_id)
            
            if not university:
                return JsonResponse({'success': False, 'message': 'University not found'}, status=404)

            # Check if student qualifies for the university (APS score)
            if profile.stored_aps_score is not None and university['minimum_aps'] <= profile.stored_aps_score:
                # Get current selected universities from profile
                selected_unis = profile.selected_universities or []
                
                # Check if university is already selected
                if uni_id not in selected_unis:
                    # Add university to selected list
                    selected_unis.append(uni_id)
                    profile.selected_universities = selected_unis
                    profile.application_count = len(selected_unis)
                    profile.save()
                    # Create application status
                    ApplicationStatus.objects.get_or_create(
                        student=profile,
                        university_id=uni_id,
                        defaults={'status': 'pending'}
                    )
                    message = f'Successfully selected {university["name"]}.'
                else:
                    # University is already selected, no change but still success
                    message = f'{university["name"]} is already in your selected list.'
                # Prepare selected university details for frontend
                selected_university = {
                    'id': university['id'],
                    'name': university['name'],
                    'due_date': university.get('due_date', ''),
                    'application_fee': university.get('application_fee', ''),
                    'detail_url': reverse('helper:university_detail', args=[university['id']]),
                }
                return JsonResponse({
                    'success': True,
                    'message': message,
                    'application_count': profile.application_count,
                    'selected_university': selected_university
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': f'Your APS score ({profile.stored_aps_score}) does not meet the minimum requirement ({university["minimum_aps"]}) for {university["name"]}.'
                })
        except Exception as e:
            logger.error(f"Error in select_university: {str(e)}")
            return JsonResponse({'success': False, 'message': 'An unexpected error occurred. Please try again.'}, status=500)
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)

@login_required
def deselect_university(request, uni_id):
    """Handle university deselection."""
    profile = get_object_or_404(StudentProfile, user=request.user)
    university = get_university_by_id(uni_id)
    
    if not university:
        messages.error(request, "University not found.")
        return redirect('helper:universities_list')
    
    # Get current selected universities from profile
    selected_unis = profile.selected_universities or []
    
    if uni_id in selected_unis:
        # Remove university from selected list
        selected_unis.remove(uni_id)
        profile.selected_universities = selected_unis
        profile.application_count = len(selected_unis)
        profile.save()
        
        # Remove application status
        ApplicationStatus.objects.filter(
            student=profile,
            university_id=uni_id
        ).delete()
        
        messages.success(request, f"Successfully removed {university['name']} from your selections.")
    else:
        messages.info(request, f"{university['name']} was not in your selections.")
        
    return redirect('helper:universities_list')

@login_required
def application_list(request):
    """Display list of applications."""
    profile = get_object_or_404(StudentProfile, user=request.user)
    applications = ApplicationStatus.objects.filter(student=profile)

    # Build a dict of universities by ID for fast lookup in template
    all_static_universities = get_all_universities()
    universities_by_id = {uni['id']: uni for uni in all_static_universities}

    # Check payment proof status for each application
    for application in applications:
        payment_proof = DocumentUpload.objects.filter(
            user=request.user,
            document_type='payment_proof',
            university__id=application.university_id
        ).first()
        if payment_proof:
            time_since_upload = timezone.now() - payment_proof.uploaded_at
            if time_since_upload.total_seconds() >= 24 * 3600:
                application.payment_verified = True
                application.save()
        else:
            if application.status != 'not_started':
                application.status = 'not_started'
                application.payment_verified = False
                application.save()

    # Prepare data for fee calculation
    universities_data_for_fee_calc = []
    application_fees_dict_for_template = {}
    for application in applications:
        static_uni_data = universities_by_id.get(application.university_id)
        fee = '0'
        if static_uni_data:
            fee = static_uni_data.get('application_fee', '0')
            application_fees_dict_for_template[static_uni_data['name']] = fee
        universities_data_for_fee_calc.append({
            'university': static_uni_data,
            'application_fee': fee
        })

    # Calculate payment breakdown using shared function
    payment_breakdown, total_university_fee = calculate_application_fees(universities_data_for_fee_calc)
    package_cost = profile.get_subscription_fee()
    total_payment = total_university_fee + package_cost

    context = {
        'applications': applications,
        'universities_by_id': universities_by_id,
        'payment_breakdown': payment_breakdown,
        'total_university_fee': total_university_fee,
        'package_cost': package_cost,
        'total_payment': total_payment,
        'student_profile': profile,
        'application_fees': application_fees_dict_for_template
    }
    return render(request, 'helper/application_list.html', context)

@login_required
def application_detail(request, app_id):
    """Display application details."""
    profile = get_object_or_404(StudentProfile, user=request.user)
    application = get_object_or_404(ApplicationStatus, id=app_id, student=profile)
    all_static_universities = get_all_universities()
    universities_by_id = {uni['id']: uni for uni in all_static_universities}
    university = universities_by_id.get(application.university_id)
    payment_proof = DocumentUpload.objects.filter(
        user=request.user,
        document_type='payment_proof',
        university__id=application.university_id
    ).first()
    time_since_upload = None
    if payment_proof:
        time_since_upload = timezone.now() - payment_proof.uploaded_at
        if time_since_upload.total_seconds() >= 24 * 3600:
            application.payment_verified = True
            application.save()
    context = {
        'application': application,
        'university': university,
        'payment_proof': payment_proof,
        'time_since_upload': time_since_upload
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
        # 'university' here is a DB model instance
        university_db_instance = get_object_or_404(University, id=uni_id) 
        
        static_uni_data = get_university_by_id(university_db_instance.id)
        application_fee = "Not specified"
        if static_uni_data:
            application_fee = static_uni_data.get('application_fee', "Not specified")
        
        subscription_payment = DocumentUpload.objects.filter(
            user=request.user,
            document_type='subscription_payment',
            verified=True
        ).first()
        
        if not subscription_payment:
            messages.error(request, "Please pay and verify your subscription fee before applying to universities.")
            return redirect('helper:pay_subscription_fee')
        
        application, created = ApplicationStatus.objects.get_or_create(
            student=profile,
            university=university_db_instance,
            defaults={
                'status': 'not_started',
                'payment_verified': False
            }
        )
        
        if application_fee.upper() == "FREE":
            application.status = 'pending'
            application.payment_verified = True
            application.save()
            messages.success(request, f"Application to {university_db_instance.name} has been initiated. No application fee required.")
            return redirect('helper:application_detail', app_id=application.id)
        
        if request.method == 'POST':
            if request.FILES.get('payment_proof'):
                # Create the document upload
                payment_proof = DocumentUpload.objects.create(
                    user=request.user,
                    document_type='payment_proof',
                    file=request.FILES['payment_proof'],
                    university=university_db_instance
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
            'university': university_db_instance, # Pass the DB model instance
            'application': application,
            'application_fee': application_fee, # This is the string value "R100", "Free", etc.
            'bank_details': bank_details,
            'student_profile': profile,
            'total_payment': f'R{total_payment}',
            'is_free_university': application_fee.upper() == "FREE"
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
    
    applications = ApplicationStatus.objects.filter(
        student=profile,
        university__in=profile.selected_universities.all()
    ).select_related('university')
    
    pending_applications = []
    paid_applications = [] # Not strictly used later, but good for clarity
    
    for application in applications:
        payment_proof = DocumentUpload.objects.filter(
            user=request.user,
            document_type='payment_proof',
            university=application.university
        ).first()
        
        if payment_proof and payment_proof.verified:
            paid_applications.append(application)
        else:
            pending_applications.append(application)
    
    universities_data_for_fee_calc = []
    for application in applications: # Iterate over all selected applications to calculate total fee
        static_uni_data = get_university_by_id(application.university.id)
        fee_str = '0'
        if static_uni_data:
            fee_str = static_uni_data.get('application_fee', '0')
        
        universities_data_for_fee_calc.append({
            # 'university' key here is not used by calculate_application_fees, only 'application_fee'
            'application_fee': fee_str 
        })
    
    payment_breakdown, total_university_fee = calculate_application_fees(universities_data_for_fee_calc)
    
    package_cost = profile.get_subscription_fee()
    total_payment = total_university_fee + package_cost
    
    bank_details = {
        'bank_name': 'Standard Bank',
        'account_holder': 'Varsity Plug',
        'account_number': '1234567890',
        'branch_code': '051001',
        'reference': f'VP-SUB-ALL-{profile.user.username}-{int(time.time())}' # Modified reference for all
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
        'applications': applications, # Full application objects for the template to list
        'pending_applications': pending_applications, 
        # 'paid_applications': paid_applications, # If needed by template
        'payment_breakdown': payment_breakdown, # List of {'name': ..., 'fee': ...}
        'total_university_fee': total_university_fee,
        'package_cost': package_cost,
        'total_payment': total_payment,
        'bank_details': bank_details,
        'student_profile': profile
    }
    
    return render(request, 'helper/pay_all_fees.html', context)

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
    profile = get_object_or_404(StudentProfile, user=request.user)
    all_static_universities = get_all_universities()
    universities_data = []

    if profile.stored_aps_score is not None:
        qualified_list = [
            uni for uni in all_static_universities
            if uni['minimum_aps'] <= profile.stored_aps_score
        ]
        qualified_list.sort(key=lambda x: x['minimum_aps'])

        for uni in qualified_list:
            uni_data_for_api = uni.copy()
            uni_data_for_api['detail_url'] = reverse('helper:university_detail', args=[uni['id']])
            # uni_data_for_api['select_url'] = reverse('helper:select_university', args=[uni['id']]) # select_university would change
            universities_data.append(uni_data_for_api)
            
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
    applications = ApplicationStatus.objects.filter(student=profile)
    payments = Payment.objects.filter(user=request.user)
    documents = DocumentUpload.objects.filter(
        user=request.user,
        document_type__in=['payment_proof', 'subscription_payment']
    )
    all_static_universities = get_all_universities()
    universities_by_id = {uni['id']: uni for uni in all_static_universities}
    subscription_payment_doc = DocumentUpload.objects.filter(
        user=request.user,
        document_type='subscription_payment'
    ).first()
    subscription_status = "Not Paid"
    if subscription_payment_doc:
        time_since_upload = timezone.now() - subscription_payment_doc.uploaded_at
        if subscription_payment_doc.verified or time_since_upload.total_seconds() >= 24 * 3600:
             if not subscription_payment_doc.verified:
                 subscription_payment_doc.verified = True
                 subscription_payment_doc.save()
             subscription_status = "Verified"
        else:
            subscription_status = "Pending Verification"
            minutes_ago = int(time_since_upload.total_seconds() / 60)
            subscription_status += f" (Uploaded {minutes_ago} minutes ago)"
    total_application_fees_value = 0
    for application in applications:
        payment_proof_doc = DocumentUpload.objects.filter(
            user=request.user,
            document_type='payment_proof',
            university__id=application.university_id
        ).first()
        static_uni_data = universities_by_id.get(application.university_id)
        application_fee_str = "0"
        if static_uni_data:
            application_fee_str = static_uni_data.get('application_fee', "0")
        current_app_fee_value = 0
        if application_fee_str.upper() != "FREE" and application_fee_str != "0" and application_fee_str != "Not specified" and application_fee_str != "Varies":
            try:
                current_app_fee_value = int(application_fee_str.replace('R', '').strip())
            except ValueError:
                current_app_fee_value = 0
        if application_fee_str.upper() == "FREE":
            application.payment_verified = True
            application.status = 'pending'
        elif payment_proof_doc:
            if payment_proof_doc.verified or (timezone.now() - payment_proof_doc.uploaded_at).total_seconds() >= 24*3600:
                if not payment_proof_doc.verified:
                    payment_proof_doc.verified = True
                    payment_proof_doc.save()
                application.payment_verified = True
                application.status = 'pending'
            else:
                application.payment_verified = False
                application.status = 'pending'
        else:
            application.payment_verified = False
            application.status = 'not_started'
        application.save()
        if application.payment_verified and application_fee_str.upper() != "FREE":
            total_application_fees_value += current_app_fee_value
    display_total_application_fees = 0
    application_fees_context_dict = {}
    for app_status in applications:
        static_data = universities_by_id.get(app_status.university_id)
        fee_val_str = "0"
        if static_data:
            fee_val_str = static_data.get('application_fee', "0")
            application_fees_context_dict[static_data['name']] = fee_val_str
        if fee_val_str.upper() != "FREE" and fee_val_str != "0" and fee_val_str != "Not specified" and fee_val_str != "Varies":
            try:
                display_total_application_fees += int(fee_val_str.replace('R', '').strip())
            except ValueError:
                pass
    subscription_fee_value = profile.get_subscription_fee()
    context = {
        'profile': profile,
        'applications': applications,
        'universities_by_id': universities_by_id,
        'payments': payments,
        'documents': documents,
        'subscription_payment_doc': subscription_payment_doc,
        'subscription_status': subscription_status,
        'total_application_fees': display_total_application_fees,
        'subscription_fee': subscription_fee_value,
        'total_amount': display_total_application_fees + subscription_fee_value,
        'application_fees_dict': application_fees_context_dict
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
    all_static_universities = get_all_universities()
    universities_by_id = {uni['id']: uni for uni in all_static_universities}
    for application in applications:
        payment_proof = DocumentUpload.objects.filter(
            user=request.user,
            document_type='payment_proof',
            university__id=application.university_id
        ).first()
        payment, created = Payment.objects.get_or_create(
            user=request.user,
            university=universities_by_id.get(application.university_id, {}).get('name', ''),
            defaults={'payment_status': 'not_paid'}
        )
        if payment_proof:
            if payment_proof.verified:
                application.payment_verified = True
                application.status = 'pending'
                payment.payment_status = 'paid'
            else:
                application.payment_verified = False
                application.status = 'pending'
                payment.payment_status = 'pending'
            application.save()
            payment.save()
        else:
            if application.status != 'not_started':
                application.status = 'not_started'
                application.payment_verified = False
                application.save()
            payment.payment_status = 'not_paid'
            payment.save()
    context = {
        'applications': applications,
        'universities_by_id': universities_by_id,
        'payments': payments,
        'documents': documents,
        'student_profile': profile
    }
    return render(request, 'helper/payments.html', context)

@login_required
def payment_statuses(request):
    """API endpoint to get payment statuses for all applications."""
    student_profile = get_object_or_404(StudentProfile, user=request.user)
    applications = ApplicationStatus.objects.filter(student=student_profile)
    
    statuses = []
    for application in applications:
        payment = DocumentUpload.objects.filter(
            student=student_profile,
            document_type='payment_proof',
            university_id=application.university_id
        ).first()
        
        status = {
            'id': application.id,
            'university_id': application.university_id,
            'status': 'paid' if payment and payment.verified else 'pending' if payment else 'not_paid'
        }
        statuses.append(status)
    
    return JsonResponse(statuses, safe=False)