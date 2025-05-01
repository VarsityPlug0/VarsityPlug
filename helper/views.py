from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.safestring import mark_safe
# Import reverse for generating URLs in the view
from django.urls import reverse
from .forms import DocumentUploadForm
from .models import DocumentUpload, University, StudentProfile
from .faculty_data import FACULTY_COURSES, FACULTIES_OPEN
from django_ratelimit.decorators import ratelimit
from django.http import JsonResponse, HttpResponseNotFound
from django.utils.html import escape
import openai
from django.conf import settings
import logging
# Import json and DjangoJSONEncoder
import json
from django.core.serializers.json import DjangoJSONEncoder


# Set up logging
logger = logging.getLogger(__name__) # Use __name__ for logger name

# Set up OpenAI API key
openai.api_key = settings.OPENAI_API_KEY

# Valid NSC subjects (assuming this list is correct and complete)
NSC_SUBJECTS = [
    "Accounting", "Agricultural Sciences", "Business Studies",
    "Computer Applications Technology", "Consumer Studies", "Dramatic Arts",
    "Economics", "Engineering Graphics and Design", "Geography", "History",
    "Information Technology", "Life Sciences", "Mathematics",
    "Mathematical Literacy", "Music", "Physical Sciences", "Religion Studies",
    "Tourism", "Visual Arts", "Afrikaans Home Language",
    "Afrikaans First Additional Language", "English Home Language",
    "English First Additional Language", "IsiNdebele Home Language",
    "IsiNdebele First Additional Language", "IsiXhosa Home Language",
    "IsiXhosa First Additional Language", "IsiZulu Home Language",
    "IsiZulu First Additional Language", "Sepedi Home Language",
    "Sepedi First Additional Language", "Sesotho Home Language",
    "Sesotho First Additional Language", "Setswana Home Language",
    "Setswana First Additional Language", "Siswati Home Language",
    "Siswati First Additional Language", "Tshivenda Home Language",
    "Tshivenda First Additional Language", "Xitsonga Home Language",
    "Xitsonga First Additional Language", "Life Orientation",
]

# Constants for University Info (Consider moving to models or settings if more dynamic)
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
    # Use logger associated with this module
    local_logger = logging.getLogger(__name__)
    if not marks or not isinstance(marks, dict) or len(marks) != 7:
        local_logger.debug(f"APS calculation failed: Invalid marks data type or length ({len(marks) if isinstance(marks, dict) else 'N/A'})")
        return None

    aps = 0
    subjects_processed = set() # To track processed subjects

    for subject, mark in marks.items():
         # Skip if already processed (e.g., if dict somehow had duplicates)
        if subject in subjects_processed:
            continue

        if mark is None:
            local_logger.debug(f"APS calculation failed: Missing mark for {subject}")
            return None # Missing mark is invalid

        # Ensure mark is a number (int or float)
        try:
            mark_num = float(mark)
        except (ValueError, TypeError):
             local_logger.debug(f"APS calculation failed: Invalid mark type for {subject}: {mark} ({type(mark)})")
             return None # Non-numeric mark is invalid

        if not 0 <= mark_num <= 100:
            local_logger.debug(f"APS calculation failed: Mark out of range for {subject}: {mark_num}")
            return None # Mark out of range

        # Exclude Life Orientation from APS calculation
        if subject == 'Life Orientation':
            subjects_processed.add(subject)
            continue

        # Calculate APS points based on the mark
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
        else: # 0-29
            aps += 1 # Assign 1 point even for low marks (common practice, verify if needed)

        subjects_processed.add(subject)

    # Final check: Ensure 6 subjects contributed (7 total - 1 LO)
    if len(subjects_processed) != 7 or 'Life Orientation' not in subjects_processed:
         local_logger.debug(f"APS calculation failed: Incorrect number/type of subjects processed. Processed: {subjects_processed}")
         return None

    local_logger.info(f"Calculated APS: {aps} for marks: {marks}")
    return aps

def custom_404(request, exception):
    """Handle 404 errors with a custom page."""
    return render(request, '404.html', status=404)

def home(request):
    """Render the homepage and handle action button redirects."""
    if request.method == 'POST' and 'take_action' in request.POST:
        if request.user.is_authenticated:
            return redirect('helper:dashboard_student')
        return redirect('login')
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

def register(request):
    """Handle user registration and automatic login."""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create student profile immediately after registration
            StudentProfile.objects.create(user=user)
            login(request, user)
            messages.success(request, "Registration successful! Welcome to Varsity Plug.")
            # Redirect to subscription selection after registration
            return redirect('helper:subscription_selection')
        messages.error(request, "Registration failed. Please correct the errors below.")
    else:
        form = UserCreationForm()
    return render(request, 'helper/register.html', {'form': form})

@login_required
def redirect_after_login(request):
    """Redirect authenticated users to appropriate dashboard or subscription page."""
    # Ensure student profile exists, create if necessary (e.g., for users created before profile logic)
    student_profile, created = StudentProfile.objects.get_or_create(user=request.user)
    if created:
        logger.info(f"Created missing student profile for user {request.user.username} during redirect.")

    if not student_profile.subscription_status:
        return redirect('helper:subscription_selection')
    return redirect('helper:dashboard_student')

@login_required
def subscription_selection(request):
    """Handle subscription package selection or upgrade."""
    student_profile, _ = StudentProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        package = request.POST.get('package')
        if package not in ['basic', 'standard', 'premium', 'ultimate']:
            messages.error(request, "Invalid package selected. Please try again.")
            return redirect('helper:subscription_selection')

        is_upgrade = student_profile.subscription_status
        old_package = student_profile.subscription_package

        student_profile.subscription_package = package
        student_profile.subscription_status = True # Assume subscription becomes active upon selection

        # Reset application count ONLY if upgrading to a higher tier
        # (Ultimate is highest, doesn't reset if already Ultimate)
        package_order = {'basic': 1, 'standard': 2, 'premium': 3, 'ultimate': 4}
        if is_upgrade and package_order.get(package, 0) > package_order.get(old_package, 0):
             # Only reset if moving UP the tiers
            student_profile.application_count = 0
            # Clear selected universities on upgrade to avoid confusion with limits
            student_profile.selected_universities.clear()
            upgrade_message = f"You have successfully upgraded to the {package.capitalize()} Package! Your application count and selections have been reset."
        elif is_upgrade:
             upgrade_message = f"You have successfully changed to the {package.capitalize()} Package!" # No reset if same or lower tier
        else:
             upgrade_message = f"You have successfully subscribed to the {package.capitalize()} Package!"


        student_profile.save()
        messages.success(request, upgrade_message)
        return redirect('helper:dashboard_student')

    packages = [
        {'name': 'Basic Package', 'price': 'R400', 'value': 'basic', 'includes': 'Varsity Plug applies for you: Up to 3 university applications + document uploads + tracking'},
        {'name': 'Standard Package', 'price': 'R600', 'value': 'standard', 'includes': 'Varsity Plug applies for you: Up to 5 applications + Application Fee Guidance + Support'},
        {'name': 'Premium Package', 'price': 'R800', 'value': 'premium', 'includes': 'Varsity Plug applies for you: Up to 7 applications + Support + Course Advice + WhatsApp Chat'},
        {'name': 'Ultimate Package', 'price': 'R1000', 'value': 'ultimate', 'includes': 'Varsity Plug applies for you: Unlimited applications + Full concierge service + All support features'},
    ]

    return render(request, 'helper/subscription_selection.html', {
        'packages': packages,
        'is_upgrade': student_profile.subscription_status,
        'current_package': student_profile.subscription_package
    })

@login_required
def dashboard_student(request):
    """Render the student dashboard, handling marks/doc uploads, recommendations, and qualified universities."""
    local_logger = logging.getLogger(__name__)
    local_logger.debug(f"Accessing dashboard_student for user {request.user.username}")
    try:
        # Ensure profile exists
        student_profile, created = StudentProfile.objects.get_or_create(user=request.user)
        if created:
            local_logger.warning(f"Created missing profile for user {request.user.username} in dashboard.")
            # If profile was just created, they likely need to subscribe first
            return redirect('helper:subscription_selection')

        # Check subscription status
        if not student_profile.subscription_status:
             messages.info(request, "Please select a subscription package to access the dashboard features.")
             return redirect('helper:subscription_selection')


        form = DocumentUploadForm() # Initialize doc upload form
        documents = DocumentUpload.objects.filter(user=request.user).order_by('-uploaded_at')

        # Prepare selected universities with due_date and application_fee
        selected_universities_qs = student_profile.selected_universities.all()
        selected_universities_list = [ # Changed name to avoid clash
            {
                'id': uni.id,
                'name': uni.name,
                'due_date': UNIVERSITY_DUE_DATES.get(uni.name, "TBD"),
                'application_fee': APPLICATION_FEES_2025.get(uni.name, "Not available")
            } for uni in selected_universities_qs
        ]

        marks = student_profile.marks if student_profile.marks else {}

        # Prepare marks list for the form, pre-filling if marks exist
        marks_list = [
            {'label': 'Home Language', 'key_prefix': 'hl', 'mark': '', 'options': [s for s in NSC_SUBJECTS if 'Home Language' in s], 'selected_subject': ''},
            {'label': 'First Additional Language', 'key_prefix': 'fal', 'mark': '', 'options': [s for s in NSC_SUBJECTS if 'First Additional Language' in s], 'selected_subject': ''},
            {'label': 'Mathematics or Mathematical Literacy', 'key_prefix': 'math', 'mark': '', 'options': ['Mathematics', 'Mathematical Literacy'], 'selected_subject': ''},
            {'label': 'Life Orientation', 'key_prefix': 'lo', 'mark': 0, 'options': ['Life Orientation'], 'selected_subject': 'Life Orientation'}, # Fixed LO
            {'label': 'Elective 1', 'key_prefix': 'elec1', 'mark': '', 'options': [s for s in NSC_SUBJECTS if 'Language' not in s and s not in ['Mathematics', 'Mathematical Literacy', 'Life Orientation']], 'selected_subject': ''},
            {'label': 'Elective 2', 'key_prefix': 'elec2', 'mark': '', 'options': [s for s in NSC_SUBJECTS if 'Language' not in s and s not in ['Mathematics', 'Mathematical Literacy', 'Life Orientation']], 'selected_subject': ''},
            {'label': 'Elective 3', 'key_prefix': 'elec3', 'mark': '', 'options': [s for s in NSC_SUBJECTS if 'Language' not in s and s not in ['Mathematics', 'Mathematical Literacy', 'Life Orientation']], 'selected_subject': ''},
        ]

        # Pre-fill marks_list based on existing student_profile.marks
        if marks:
            elective_indices = [4, 5, 6] # Indices for electives
            current_elective_idx = 0
            for subject, mark_value in marks.items():
                found = False
                for item in marks_list:
                    if item['label'] == 'Home Language' and 'Home Language' in subject:
                        item['selected_subject'] = subject
                        item['mark'] = mark_value
                        found = True; break
                    elif item['label'] == 'First Additional Language' and 'First Additional Language' in subject:
                        item['selected_subject'] = subject
                        item['mark'] = mark_value
                        found = True; break
                    elif item['label'] == 'Mathematics or Mathematical Literacy' and subject in item['options']:
                         item['selected_subject'] = subject
                         item['mark'] = mark_value
                         found = True; break
                    elif item['label'] == 'Life Orientation' and subject == 'Life Orientation':
                         item['mark'] = 0 # Always 0 for display
                         found = True; break # Should already be set

                if not found and subject != 'Life Orientation' and 'Language' not in subject and subject not in ['Mathematics', 'Mathematical Literacy']:
                     # Assign to the next available elective slot
                     if current_elective_idx < len(elective_indices):
                          idx = elective_indices[current_elective_idx]
                          marks_list[idx]['selected_subject'] = subject
                          marks_list[idx]['mark'] = mark_value
                          current_elective_idx += 1


        # Handle POST requests for marks or document uploads
        if request.method == 'POST':
            if 'submit_marks' in request.POST:
                # --- Marks Submission Logic ---
                new_marks = {}
                subjects_entered_count = 0
                selected_subjects_set = set()
                has_error = False

                for i in range(7):
                    if i == 3: # Life Orientation - fixed value
                        subject_key = 'Life Orientation'
                        mark_key = '0' # Mark is always 0 for LO
                        subject_name = 'Life Orientation'
                    else:
                        subject_key = f'subject_{i}'
                        mark_key = f'mark_{i}'
                        subject_name = request.POST.get(subject_key)
                        mark_value_str = request.POST.get(mark_key, '').strip()

                    # Validation for non-LO subjects
                    if i != 3:
                        if not subject_name or subject_name == "":
                             messages.error(request, f"Missing subject for entry {i+1}.")
                             has_error = True; break
                        if subject_name not in NSC_SUBJECTS:
                            messages.error(request, f"Invalid subject selected: {escape(subject_name)}. Please select a valid NSC subject.")
                            has_error = True; break
                        if subject_name in selected_subjects_set:
                             messages.error(request, f"Duplicate subject selected: {escape(subject_name)}. Please select unique subjects.")
                             has_error = True; break
                        if not mark_value_str:
                             messages.error(request, f"Missing mark for {escape(subject_name)}.")
                             has_error = True; break
                        try:
                            mark_value = int(mark_value_str)
                            if not 0 <= mark_value <= 100:
                                messages.error(request, f"Mark for {escape(subject_name)} must be between 0 and 100.")
                                has_error = True; break
                            new_marks[subject_name] = mark_value
                            selected_subjects_set.add(subject_name)
                            subjects_entered_count += 1
                        except (ValueError, TypeError):
                            messages.error(request, f"Invalid mark '{escape(mark_value_str)}' for {escape(subject_name)}. Please enter a whole number.")
                            has_error = True; break
                    else: # Handle LO
                        new_marks[subject_name] = 0
                        selected_subjects_set.add(subject_name)
                        subjects_entered_count += 1

                # Further validation after loop
                if not has_error:
                    if subjects_entered_count != 7:
                        messages.error(request, f"Please ensure exactly 7 unique subjects are entered (including Life Orientation). You entered {subjects_entered_count}.")
                        has_error = True

                    # Check required subject types
                    has_home_language = any('Home Language' in s for s in selected_subjects_set)
                    has_fal = any('First Additional Language' in s for s in selected_subjects_set)
                    has_math = any(s in ['Mathematics', 'Mathematical Literacy'] for s in selected_subjects_set)
                    has_lo = 'Life Orientation' in selected_subjects_set

                    if not (has_home_language and has_fal and has_math and has_lo):
                        missing = []
                        if not has_home_language: missing.append("Home Language")
                        if not has_fal: missing.append("First Additional Language")
                        if not has_math: missing.append("Mathematics or Math Literacy")
                        if not has_lo: missing.append("Life Orientation")
                        messages.error(request, f"Missing required subject types: {', '.join(missing)}.")
                        has_error = True

                if not has_error:
                    student_profile.marks = new_marks
                    aps_score = calculate_aps(new_marks) # Recalculate APS
                    student_profile.stored_aps_score = aps_score # Store the new score
                    student_profile.save()
                    local_logger.info(f"Marks updated and APS stored for user {request.user.username}: {aps_score}")

                    if aps_score is None:
                        messages.warning(request, "Marks saved, but APS score could not be calculated. Please ensure all marks are valid (0-100).")
                    else:
                        messages.success(request, f"Marks updated successfully! Your new APS score is {aps_score}.")
                # Redirect even if there was an error to show messages
                return redirect('helper:dashboard_student')

            else: # Assumed document upload if not marks submission
                # --- Document Upload Logic ---
                form = DocumentUploadForm(request.POST, request.FILES)
                if form.is_valid():
                    doc = form.save(commit=False)
                    doc.user = request.user
                    document_type = form.cleaned_data['document_type'] # Use cleaned data
                    university_id = request.POST.get('university_id') # Get hidden field

                    # Handle specific linking for payment proof
                    if document_type == 'payment_proof' and university_id:
                        try:
                            university = University.objects.get(id=university_id)
                            doc.university = university # Link document to university
                            doc.save() # Save with link
                            messages.success(request, f"Proof of payment for {university.name} uploaded successfully!")
                            local_logger.info(f"Payment proof uploaded by {request.user.username} for {university.name}: {doc.file.name}")
                        except University.DoesNotExist:
                            messages.error(request, "Invalid university specified for payment proof.")
                            local_logger.error(f"Invalid university ID {university_id} for payment proof by {request.user.username}")
                            # Don't save the doc if uni is invalid for PoP
                            return redirect('helper:dashboard_student') # Redirect back
                    else:
                        # Save generic documents or PoP without specific uni ID if needed
                        doc.university = None # Ensure no accidental link
                        doc.save()
                        messages.success(request, f"{doc.get_document_type_display()} uploaded successfully!")
                        local_logger.info(f"Document ({doc.get_document_type_display()}) uploaded by {request.user.username}: {doc.file.name}")

                    return redirect('helper:dashboard_student')
                else:
                     # Form is not valid, add form errors to messages
                     for field, errors in form.errors.items():
                         for error in errors:
                              messages.error(request, f"Error in {field}: {error}")
                     local_logger.error(f"Document upload failed for {request.user.username}: {form.errors.as_json()}")
                     # No redirect here, re-render the page with the invalid form potentially?
                     # Or redirect like before:
                     return redirect('helper:dashboard_student')


        # --- GET Request Logic or after POST redirect ---
        # Use stored APS score for consistency
        student_aps = student_profile.stored_aps_score
        # Recalculate only if stored score is missing but marks exist (e.g., old data)
        if student_aps is None and student_profile.marks:
            local_logger.debug(f"No stored APS for {request.user.username}, calculating from marks")
            student_aps = calculate_aps(student_profile.marks)
            if student_aps is not None:
                student_profile.stored_aps_score = student_aps
                student_profile.save()
                local_logger.info(f"Calculated and stored APS for {request.user.username}: {student_aps}")
            else:
                 local_logger.warning(f"Failed to calculate APS for {request.user.username} from existing marks: {student_profile.marks}")
                 # Optionally add a message if calculation failed from existing marks
                 # messages.warning(request, "Could not calculate APS from your saved marks. Please re-submit them.")


        # Fetch university recommendations (remains the same logic)
        recommendations = []
        if student_aps is not None:
            try:
                # Fetching only top 5 recommendations
                eligible_unis_recommend = University.objects.filter(minimum_aps__lte=student_aps).order_by('?')[:5] # Randomize recommendations slightly
                recommendations = [
                    {
                        'id': uni.id,
                        'name': uni.name,
                        'description': uni.description or f"Explore opportunities at {uni.name}, known for its excellent programs.",
                        'due_date': UNIVERSITY_DUE_DATES.get(uni.name, "TBD"),
                        'application_fee': APPLICATION_FEES_2025.get(uni.name, "Not available"),
                         # Generate URLs needed for JS card generation
                        'detail_url': reverse('helper:university_detail', args=[uni.id]),
                        'select_url': reverse('helper:select_university', args=[uni.id])
                    } for uni in eligible_unis_recommend
                ]
                local_logger.info(f"Fetched {len(recommendations)} university recommendations for APS {student_aps} for user {request.user.username}")
                # Don't show message if no recommendations, maybe they just don't qualify for top 5
                # if not recommendations:
                #     logger.warning(f"No recommendation universities found for APS {student_aps} for user {request.user.username}")
                #     # messages.info(request, "No university recommendations available currently.") # Avoid repetitive message
            except Exception as e:
                local_logger.error(f"Error fetching recommendations for {request.user.username}: {str(e)}", exc_info=True)
                messages.error(request, "Unable to fetch university recommendations at this time.")

        # **** CHANGE FOR NEW DISPLAY METHOD ****
        # Fetch qualified universities and prepare for JSON embedding
        qualified_universities_list = [] # Use a distinct name
        if student_aps is not None:
            try:
                qualified_qs = University.objects.filter(minimum_aps__lte=student_aps).order_by('name')
                qualified_universities_list = [
                    {
                        'id': uni.id,
                        'name': uni.name,
                        'location': uni.province or "South Africa",
                        'due_date': UNIVERSITY_DUE_DATES.get(uni.name, "TBD"),
                        'application_fee': APPLICATION_FEES_2025.get(uni.name, "Not available"),
                        # Generate URLs needed for JS card generation
                        'detail_url': reverse('helper:university_detail', args=[uni.id]),
                        'select_url': reverse('helper:select_university', args=[uni.id])
                    } for uni in qualified_qs
                ]
                local_logger.debug(f"Fetched {len(qualified_universities_list)} qualified universities for APS {student_aps}")
            except Exception as e:
                local_logger.error(f"Error fetching qualified universities for {request.user.username}: {str(e)}", exc_info=True)
                messages.error(request, "Unable to fetch qualified universities at this time.")

        # Convert the list to a JSON string for embedding in the template
        # Use DjangoJSONEncoder to handle potential special types like dates/decimals if they were included
        qualified_universities_json = json.dumps(qualified_universities_list, cls=DjangoJSONEncoder)
        # **** END OF CHANGE ****

        context = {
            'form': form, # Document upload form
            'documents': documents,
            'selected_universities': selected_universities_list, # Pass the processed list for the table
            'recommended_universities': recommendations, # For the recommendations carousel
            'universities': qualified_universities_json, # **** CHANGED: Pass JSON string for the dynamic display ****
            'student_profile': student_profile,
            'marks_list': marks_list, # For pre-filling marks form
            'nsc_subjects': NSC_SUBJECTS, # For dropdowns
            'UNIVERSITY_DUE_DATES': UNIVERSITY_DUE_DATES, # Maybe remove if only used here?
            'student_aps': student_aps, # Pass calculated APS score
        }
        return render(request, 'helper/dashboard_student.html', context)

    except StudentProfile.DoesNotExist:
         logger.error(f"StudentProfile does not exist for user {request.user.username} in dashboard_student")
         messages.error(request, "Your student profile is missing. Please contact support.")
         # Redirect to a safe page, maybe home or logout?
         return redirect('home') # Or logout?

    except Exception as e:
        local_logger.error(f"Unexpected error in dashboard_student view for {request.user.username}: {str(e)}", exc_info=True)
        messages.error(request, "An unexpected error occurred loading your dashboard. Please try again later or contact support.")
        # Redirect to a safe page or render generic error page
        return render(request, 'helper/error.html', {'error': 'An unexpected error occurred loading the dashboard'})


# ... (rest of the views remain the same) ...

@login_required
def dashboard_guide(request):
    """Render the guide dashboard for non-student users."""
    return render(request, 'helper/dashboard_guide.html')

@login_required
def delete_document(request, doc_id):
    """Delete a user's uploaded document."""
    document = get_object_or_404(DocumentUpload, id=doc_id, user=request.user)
    if request.method == 'POST':
        # Optionally: delete the file from storage first
        # document.file.delete(save=False) # Set save=False if deleting model instance right after
        document.delete()
        messages.success(request, "Document deleted successfully!")
        logger.info(f"Document {doc_id} deleted by {request.user.username}")
    return redirect('helper:dashboard_student')

@login_required
def edit_document(request, doc_id):
    """Edit an existing document upload."""
    document = get_object_or_404(DocumentUpload, id=doc_id, user=request.user)
    if request.method == 'POST':
        # Pass instance to pre-fill the form for editing
        form = DocumentUploadForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            form.save()
            messages.success(request, "Document updated successfully!")
            logger.info(f"Document {doc_id} updated by {request.user.username}")
            return redirect('helper:dashboard_student')
        else:
             # Handle invalid form during edit
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Update failed for {field}: {error}")
            logger.error(f"Document update failed for {request.user.username}: {form.errors.as_json()}")
            # Re-render potentially? Or redirect back showing errors
            return redirect('helper:dashboard_student') # Simple redirect back for now

    # For GET request, we might want to show the edit form in a modal or separate page
    # Currently, this view only handles POST for editing via modal submission likely
    # Redirecting back if accessed via GET might be appropriate if edit is modal-only
    return redirect('helper:dashboard_student')


@login_required
def universities_list(request):
    """Display and manage the list of universities for selection."""
    # Use logger associated with this module
    local_logger = logging.getLogger(__name__)
    universities = University.objects.all().order_by('name')
    student_profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    student_aps = student_profile.stored_aps_score

    if request.method == 'POST':
        selected_ids = request.POST.getlist('universities')
        try:
            # Validate selected IDs are valid integers
            valid_selected_ids = []
            for uni_id in selected_ids:
                try:
                    valid_selected_ids.append(int(uni_id))
                except (ValueError, TypeError):
                     messages.error(request, f"Invalid university ID received: {escape(uni_id)}")
                     return redirect('helper:universities_list')

            selected_universities_qs = University.objects.filter(id__in=valid_selected_ids)
            new_application_count = len(selected_universities_qs)

            # Check against subscription limit (Ultimate has no limit check needed technically)
            limit = student_profile.get_application_limit()
            can_apply_more = student_profile.can_apply() # Checks both limit and status

            if not can_apply_more or (limit is not None and new_application_count > limit) :
                 # Handle case where limit is None (Ultimate) separately if needed, but check should be fine
                upgrade_link = reverse('helper:subscription_selection')
                message = (
                    f"Your '{student_profile.get_subscription_package_display()}' package allows "
                    f"{limit if limit is not None else 'unlimited'} applications. "
                    f"Selecting {new_application_count} universities exceeds this limit or your current count ({student_profile.application_count}). "
                    f'<a href="{upgrade_link}" class="alert-link">Upgrade your plan?</a>'
                )
                messages.error(request, mark_safe(message))
                # Don't save changes if limit exceeded
                return redirect('helper:universities_list')

             # Check if all selected universities meet minimum APS requirement
            if student_aps is not None:
                 ineligible_unis = []
                 for uni in selected_universities_qs:
                      if uni.minimum_aps and uni.minimum_aps > student_aps:
                           ineligible_unis.append(uni.name)
                 if ineligible_unis:
                      messages.warning(request, mark_safe(
                          f"Warning: Your APS score ({student_aps}) might not meet the minimum requirement for: "
                          f"{', '.join(escape(name) for name in ineligible_unis)}. Your selections have been saved, but "
                          "admission is less likely for these."
                      ))


            # If checks pass, update the profile
            student_profile.selected_universities.set(selected_universities_qs)
            # IMPORTANT: Update application_count based on the *actual* number selected
            student_profile.application_count = new_application_count
            student_profile.save()
            messages.success(request, "Selected universities updated successfully!")
            local_logger.info(f"Selected universities updated for {request.user.username}: {new_application_count} universities")

        except Exception as e:
            local_logger.error(f"Error updating selected universities for {request.user.username}: {str(e)}", exc_info=True)
            messages.error(request, "An error occurred while updating selected universities.")
        return redirect('helper:universities_list') # Redirect back after POST

    # Prepare data for GET request
    eligible_universities = universities.filter(minimum_aps__lte=student_aps) if student_aps is not None else universities.none() # Use none() if no APS
    selected_universities_qs = student_profile.selected_universities.all()

    # Add details for selected universities display
    selected_with_details = [
        {
            'university': uni,
            'due_date': UNIVERSITY_DUE_DATES.get(uni.name, "TBD"),
            'faculties_open': FACULTIES_OPEN.get(uni.name, ["N/A"]), # Provide default
            'application_fee': APPLICATION_FEES_2025.get(uni.name, "N/A")
        } for uni in selected_universities_qs
    ]

     # Add fee/due date info to the list of eligible universities for display
    eligible_universities_with_details = []
    can_access_guidance = student_profile.can_access_fee_guidance()
    for uni in eligible_universities:
         fee_display = APPLICATION_FEES_2025.get(uni.name, "N/A")
         if not can_access_guidance and fee_display not in ["FREE", "N/A"]:
             fee_display = "Upgrade Required"

         eligible_universities_with_details.append({
             'university': uni,
             'fee': fee_display,
             'due_date': UNIVERSITY_DUE_DATES.get(uni.name, "TBD"),
             'is_selected': uni in selected_universities_qs # Check if already selected
         })


    # Calculate payment breakdown (remains similar)
    total_university_fee = 0
    payment_breakdown = []
    for uni in selected_universities_qs:
        fee_str = APPLICATION_FEES_2025.get(uni.name, "N/A")
        university_fee = 0 # Default to 0
        if "FREE" not in fee_str and "N/A" not in fee_str:
             # Try to extract the primary fee amount
             fee_parts = fee_str.split(',')
             fee_value = fee_parts[0].strip().split('(')[0].strip() # Get first part before comma or parenthesis
             try:
                 university_fee = int(fee_value.replace('R', '').strip())
             except (ValueError, AttributeError):
                 local_logger.warning(f"Could not parse fee '{fee_str}' for {uni.name}")
                 university_fee = 0 # Treat as 0 if parsing fails

        total_university_fee += university_fee
        payment_breakdown.append({
            'university': uni.name,
            'university_fee': university_fee, # Store the calculated numeric fee
            'fee_display': fee_str # Store original display string
        })

    package_costs = {'basic': 400, 'standard': 600, 'premium': 800, 'ultimate': 1000}
    package_cost = package_costs.get(student_profile.subscription_package, 0)
    total_payment = total_university_fee + package_cost

    return render(request, 'helper/universities_list.html', {
        'student_aps': student_aps,
        'eligible_universities': eligible_universities_with_details, # Pass list with details
        'selected_with_details': selected_with_details, # Pass selected list with details
        # 'APPLICATION_FEES_2025': APPLICATION_FEES_2025, # Maybe not needed directly in template now
        # 'UNIVERSITY_DUE_DATES': UNIVERSITY_DUE_DATES, # Maybe not needed directly
        'student_profile': student_profile,
        'payment_breakdown': payment_breakdown,
        'total_university_fee': total_university_fee,
        'package_cost': package_cost,
        'total_payment': total_payment,
    })


@login_required
def university_detail(request, uni_id):
    """Display details for a specific university."""
    university = get_object_or_404(University, id=uni_id)
    student_profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    application_fee = APPLICATION_FEES_2025.get(university.name, "Not available")
    due_date = UNIVERSITY_DUE_DATES.get(university.name, "TBD")
    faculties_open = FACULTIES_OPEN.get(university.name, ["Faculty information not available yet."])

    return render(request, 'helper/university_detail.html', {
        'university': university,
        'application_fee': application_fee,
        'due_date': due_date,
        'faculties_open': faculties_open,
        'student_profile': student_profile, # Pass profile for potential checks in template
    })

@login_required
def university_faculties(request, uni_id):
    """Display available faculties and courses for a university."""
    university = get_object_or_404(University, id=uni_id)
    student_profile, _ = StudentProfile.objects.get_or_create(user=request.user)

    # Get faculties and courses, providing defaults if missing
    university_faculties = FACULTIES_OPEN.get(university.name, ["Faculty list pending update."])
    university_courses = FACULTY_COURSES.get(university.name, {})

    # Structure data for template, ensuring all faculties have course lists
    faculty_courses_data = {}
    for faculty in university_faculties:
         faculty_courses_data[faculty] = university_courses.get(faculty, ["Course list pending update."])

    show_course_advice = student_profile.can_access_course_advice()
    return render(request, 'helper/university_faculties.html', {
        'university': university,
        'faculty_courses': faculty_courses_data, # Pass structured data
        'show_course_advice': show_course_advice,
    })


# --- Payment Views ---

def _get_numeric_fee(uni_name):
    """Helper to get numeric fee amount."""
    local_logger = logging.getLogger(__name__)
    fee_str = APPLICATION_FEES_2025.get(uni_name, "N/A")
    if "FREE" in fee_str or "N/A" in fee_str:
        return 0
    else:
        fee_parts = fee_str.split(',')
        fee_value = fee_parts[0].strip().split('(')[0].strip()
        try:
            return int(fee_value.replace('R', '').strip())
        except (ValueError, AttributeError):
            local_logger.warning(f"Could not parse fee '{fee_str}' for {uni_name}")
            return 0 # Treat as 0 if parsing fails


@login_required
def pay_application_fee(request, uni_id):
    """(Redirect View) Redirect to payment instructions for a single university application fee."""
    # Basic check to ensure university exists before redirecting
    get_object_or_404(University, id=uni_id)
    # Redirect to the actual instruction page
    return redirect('helper:pay_application_fee_instructions', uni_id=uni_id)

@login_required
def pay_application_fee_instructions(request, uni_id):
    """(Display View) Display payment instructions for a single university application fee."""
    student_profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    university = get_object_or_404(University, id=uni_id)
    university_fee = _get_numeric_fee(university.name)
    fee_display = APPLICATION_FEES_2025.get(university.name, "N/A")

    if fee_display == "N/A":
         messages.error(request, f"Application fee information for {university.name} is not available.")
         return redirect('helper:universities_list')
    if fee_display == "FREE":
         messages.info(request, f"No application fee is required for {university.name}.")
         return redirect('helper:universities_list') # Or redirect to dashboard?

    # Calculate total (just this uni fee + package if not yet 'paid' - how to track payment?)
    # For simplicity, just show the fee needed for this uni. Assume package fee handled separately.
    total_fee = university_fee # Fee just for this university

    # Use placeholder bank details for now
    bank_details = {
        "bank_name": "VarsityPlug Bank (Example)",
        "account_number": "9876543210",
        "account_holder": "Varsity Plug Applications",
        "branch_code": "654321",
        # CRITICAL: Reference MUST be unique and linkable to user + university
        "reference": f"VP{request.user.id}U{university.id}-{uni_id}" # Example: VP123U45-45
    }

    return render(request, 'helper/pay_application_fee_instructions.html', {
        'university': university,
        'university_fee': university_fee,
        'fee_display': fee_display,
        'total_fee': total_fee, # For this specific fee
        'bank_details': bank_details,
    })


@login_required
def pay_all_application_fees(request):
    """Display payment instructions for all selected universities' application fees."""
    local_logger = logging.getLogger(__name__)
    student_profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    selected_universities_qs = student_profile.selected_universities.all()

    if not selected_universities_qs:
        messages.warning(request, "You have not selected any universities to apply to yet.")
        return redirect('helper:universities_list')

    total_university_fee = 0
    payment_breakdown = []

    for uni in selected_universities_qs:
        university_fee = _get_numeric_fee(uni.name)
        total_university_fee += university_fee
        if university_fee > 0: # Only include unis with a fee in the breakdown
            payment_breakdown.append({
                'university': uni.name,
                'university_fee': university_fee,
                'fee_display': APPLICATION_FEES_2025.get(uni.name, "N/A")
            })

    # Add package cost to the total payment required *now*
    # This assumes package fee is paid along with application fees
    package_costs = {'basic': 400, 'standard': 600, 'premium': 800, 'ultimate': 1000}
    package_cost = package_costs.get(student_profile.subscription_package, 0)

    # How to track if package fee already paid? Need a field on StudentProfile like `package_paid = models.BooleanField(default=False)`
    # For now, let's assume it's always included if paying app fees, unless maybe already paid?
    # Add logic here based on how you track package payment status.
    # Example: if student_profile.package_paid: package_cost_to_pay = 0 else: package_cost_to_pay = package_cost
    package_cost_to_pay = package_cost # Assume it needs paying now

    total_payment = total_university_fee + package_cost_to_pay

    if total_payment == 0:
        messages.info(request, "No payment is required for your selected package and universities at this time.")
        return redirect('helper:dashboard_student') # Redirect to dashboard if nothing to pay

    # Generate a unique reference for this bulk payment
    # Example: VPPKG123-U45-U67 (VP Bulk Package for user 123, unis 45 and 67)
    uni_ids_str = "-".join(f"U{uni.id}" for uni in selected_universities_qs if _get_numeric_fee(uni.name) > 0)
    reference = f"VPBULK{request.user.id}-{uni_ids_str}"
    if package_cost_to_pay > 0:
         reference = f"VPPKG{request.user.id}-{uni_ids_str}" # Indicate package included


    bank_details = {
        "bank_name": "VarsityPlug Bank (Example)",
        "account_number": "9876543210",
        "account_holder": "Varsity Plug Applications",
        "branch_code": "654321",
        "reference": reference # Unique reference for this transaction
    }

    return render(request, 'helper/pay_all_application_fees.html', {
        'selected_universities': selected_universities_qs, # Pass the QuerySet
        'payment_breakdown': payment_breakdown,
        'total_university_fee': total_university_fee,
        'package_cost_to_pay': package_cost_to_pay, # Pass the amount needing payment now
        'total_payment': total_payment,
        'bank_details': bank_details,
        'student_profile': student_profile # Pass profile if needed in template
    })


# --- AI Chat ---
@login_required
@ratelimit(key='user', rate='10/m', method='POST') # Limit requests per user
def ai_chat(request):
    """Handle AI chat requests for user queries with input sanitization."""
    local_logger = logging.getLogger(__name__)
    if request.method != 'POST':
        local_logger.warning("Invalid request method for ai_chat (Non-POST)")
        return JsonResponse({'error': 'Invalid request method. Use POST.'}, status=405)

    # Check if user is allowed to use chat based on subscription
    student_profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    if not student_profile.can_access_chat():
         local_logger.warning(f"Chat access denied for user {request.user.username} due to subscription.")
         return JsonResponse({'error': 'Your current subscription package does not include chat support.'}, status=403)


    try:
        # Use request.body for JSON payload
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()

        # Sanitize input more thoroughly if needed, escape is basic
        # Consider libraries like bleach for more robust HTML sanitization if allowing any markup
        sanitized_message = escape(user_message)

        if not sanitized_message:
            local_logger.debug("Empty message received in ai_chat")
            return JsonResponse({'error': 'Message cannot be empty'}, status=400)

        # --- Construct context for OpenAI ---
        # Include basic user info and context if helpful for the AI
        context_info = f"User: {request.user.username}. Subscription: {student_profile.get_subscription_package_display()}. "
        if student_profile.stored_aps_score:
             context_info += f"APS Score: {student_profile.stored_aps_score}. "
        # Add more context as needed (e.g., selected universities)

        system_prompt = (
            "You are VarsityPlug Assistant, helping South African students with university applications via the VarsityPlug app. "
            "Focus ONLY on app features (marks, documents, selection limits, fees shown in app), general SA university application advice (deadlines, requirements if known), and basic career guidance related to common fields (like linking subjects to faculties). "
            "Keep answers concise, friendly, and encouraging. Use bullet points for lists. "
            "DO NOT answer questions outside this scope (e.g., specific course content, personal advice, complex financial aid details, non-SA unis, controversial topics). "
            "If asked about something outside the scope, politely state you cannot help with that specific topic and suggest contacting the university directly or VarsityPlug support for app issues. "
            "If asked about specific university requirements not programmed, state that requirements vary and they should check the university's official website or the app's university details section."
            f"Current context: {context_info}" # Inject some context
        )

        # Consider storing chat history for better context (more complex)
        messages_for_api = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": sanitized_message},
        ]

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", # Or consider newer/cheaper models if applicable
            messages=messages_for_api,
            max_tokens=150, # Limit response length
            temperature=0.6, # Slightly more focused responses
            # Add user identifier for monitoring/abuse prevention
            # user=f"varsityplug-user-{request.user.id}"
        )

        ai_response = response.choices[0].message['content'].strip()
        local_logger.info(f"AI chat response generated for user {request.user.username}")
        # Basic check for potentially refusal-like content (can be improved)
        refusal_phrases = ["cannot assist", "can't help", "outside my scope", "contact support"]
        if any(phrase in ai_response.lower() for phrase in refusal_phrases):
             local_logger.warning(f"AI response for user {request.user.username} might be a refusal: '{ai_response[:100]}...'")


        return JsonResponse({'response': ai_response}, status=200)

    except json.JSONDecodeError:
        local_logger.error("Invalid JSON in ai_chat request body")
        return JsonResponse({'error': 'Invalid request format. Send JSON.'}, status=400)
    except openai.error.AuthenticationError:
        local_logger.critical("OpenAI API authentication error. Check API key.") # Use critical for severe config issues
        # Don't expose detailed error to user
        return JsonResponse({'error': 'AI chat service configuration error. Please contact support.'}, status=500)
    except openai.error.RateLimitError:
        local_logger.warning(f"OpenAI API rate limit exceeded for user {request.user.username}")
        return JsonResponse({'error': 'AI assistant is busy. Please try again in a moment.'}, status=429)
    except openai.error.OpenAIError as e: # Catch other OpenAI errors
        local_logger.error(f"OpenAI API error for user {request.user.username}: {str(e)}", exc_info=True)
        return JsonResponse({'error': 'Could not get response from AI assistant. Please try again later.'}, status=503) # Service Unavailable
    except Exception as e:
        local_logger.error(f"Unexpected error in ai_chat for user {request.user.username}: {str(e)}", exc_info=True)
        return JsonResponse({'error': 'An unexpected error occurred. Please try again.'}, status=500)


# --- University Selection AJAX ---
@login_required
def select_university(request, uni_id):
    """Handle AJAX-based university selection."""
    # Use logger associated with this module
    local_logger = logging.getLogger(__name__)
    if request.method != 'POST': # Ensure it's a POST request
         local_logger.warning(f"Invalid method {request.method} for select_university (uni_id={uni_id})")
         return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)

    # Use select_related or prefetch_related if accessing related fields frequently
    student_profile = get_object_or_404(StudentProfile.objects.select_related('user'), user=request.user)
    university = get_object_or_404(University, id=uni_id)

    # Check if already selected
    if student_profile.selected_universities.filter(id=uni_id).exists():
        local_logger.debug(f"User {request.user.username} tried to re-select university {uni_id} ({university.name})")
        return JsonResponse({
            'success': False,
            'message': f"{university.name} is already selected."
        }, status=400) # Bad Request - already selected


    # Check subscription limits
    limit = student_profile.get_application_limit()
    current_count = student_profile.selected_universities.count() # More reliable count

    # Check if adding one more exceeds the limit (unless limit is None for Ultimate)
    if limit is not None and (current_count + 1) > limit:
        local_logger.warning(f"User {request.user.username} exceeded limit selecting uni {uni_id}. Limit: {limit}, Current: {current_count}")
        upgrade_url = reverse('helper:subscription_selection')
        message = (
            f"Your '{student_profile.get_subscription_package_display()}' package limit ({limit}) reached. "
            f'<a href="{upgrade_url}" class="alert-link">Upgrade your plan</a> to select more.'
        )
        return JsonResponse({
            'success': False,
            'message': message # Pass HTML-safe message if needed, or structure for JS
        }, status=403) # Forbidden


    # Add the university
    try:
        student_profile.selected_universities.add(university)
        # Update the stored count - safer to just re-query count after adding
        new_count = student_profile.selected_universities.count()
        student_profile.application_count = new_count # Update the denormalized count
        student_profile.save(update_fields=['application_count']) # Only save the count field

        local_logger.info(f"University {university.name} (ID: {uni_id}) selected by {request.user.username}. New count: {new_count}")
        return JsonResponse({
            'success': True,
            'message': f"{university.name} has been successfully selected!",
            'application_count': new_count # Return the updated count
        }, status=200)
    except Exception as e:
        local_logger.error(f"Error adding university {uni_id} for {request.user.username}: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': "An unexpected error occurred while selecting the university. Please try again."
        }, status=500)