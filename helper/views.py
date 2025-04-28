from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.safestring import mark_safe
from .forms import DocumentUploadForm
from .models import DocumentUpload, University, StudentProfile
from .faculty_data import FACULTY_COURSES, FACULTIES_OPEN
from django_ratelimit.decorators import ratelimit
from django.http import JsonResponse
import openai
from django.conf import settings
import logging
import json

# Set up logging
logger = logging.getLogger('helper')

# Set up OpenAI API key
openai.api_key = settings.OPENAI_API_KEY

# Valid NSC subjects
NSC_SUBJECTS = [
    "Accounting",
    "Agricultural Sciences",
    "Business Studies",
    "Computer Applications Technology",
    "Consumer Studies",
    "Dramatic Arts",
    "Economics",
    "Engineering Graphics and Design",
    "Geography",
    "History",
    "Information Technology",
    "Life Sciences",
    "Mathematics",
    "Mathematical Literacy",
    "Music",
    "Physical Sciences",
    "Religion Studies",
    "Tourism",
    "Visual Arts",
    "Afrikaans Home Language",
    "Afrikaans First Additional Language",
    "English Home Language",
    "English First Additional Language",
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
]

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
    if not marks or len(marks) != 7:
        logger.debug(f"APS calculation failed: Invalid number of marks ({len(marks)})")
        return None
    
    aps = 0
    for subject, mark in marks.items():
        if mark is None or not isinstance(mark, (int, float)) or mark < 0 or mark > 100:
            logger.debug(f"Invalid mark for {subject}: {mark}")
            return None
        if subject != 'Life Orientation':
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
    logger.info(f"Calculated APS: {aps} for marks: {marks}")
    return aps

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
            login(request, user)
            messages.success(request, "Registration successful! Welcome to Varsity Plug.")
            return redirect('helper:redirect_after_login')
        messages.error(request, "Registration failed. Please correct the errors below.")
    else:
        form = UserCreationForm()
    return render(request, 'helper/register.html', {'form': form})

@login_required
def redirect_after_login(request):
    """Redirect authenticated users to appropriate dashboard or subscription page."""
    if hasattr(request.user, 'studentprofile'):
        student_profile = request.user.studentprofile
        if not student_profile.subscription_status:
            return redirect('helper:subscription_selection')
        return redirect('helper:dashboard_student')
    return redirect('helper:dashboard_guide')

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
        student_profile.subscription_status = True

        package_order = {'basic': 1, 'standard': 2, 'premium': 3, 'ultimate': 4}
        if is_upgrade and package_order.get(package, 0) > package_order.get(old_package, 0):
            student_profile.application_count = 0
            student_profile.selected_universities.clear()

        student_profile.save()

        if is_upgrade:
            messages.success(request, f"You have successfully upgraded to the {package.capitalize()} Package! Your application count has been reset.")
        else:
            messages.success(request, f"You have successfully subscribed to the {package.capitalize()} Package!")
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
    })

@login_required
@ratelimit(key='user', rate='10/m')
def dashboard_student(request):
    """Render the student dashboard, handling marks submission, document uploads, and university recommendations."""
    try:
        student_profile, _ = StudentProfile.objects.get_or_create(user=request.user)
        form = DocumentUploadForm()
        documents = DocumentUpload.objects.filter(user=request.user).order_by('-uploaded_at')

        # Prepare selected universities with due_date and application_fee
        selected_universities = [
            {
                'id': uni.id,
                'name': uni.name,
                'due_date': UNIVERSITY_DUE_DATES.get(uni.name, "TBD"),
                'application_fee': APPLICATION_FEES_2025.get(uni.name, "Not available")
            } for uni in student_profile.selected_universities.all()
        ]

        marks = student_profile.marks if student_profile.marks else {}

        marks_list = [
            {'subject': 'Home Language', 'mark': '', 'options': [s for s in NSC_SUBJECTS if 'Home Language' in s]},
            {'subject': 'First Additional Language', 'mark': '', 'options': [s for s in NSC_SUBJECTS if 'First Additional Language' in s]},
            {'subject': 'Mathematics or Mathematical Literacy', 'mark': '', 'options': ['Mathematics', 'Mathematical Literacy']},
            {'subject': 'Life Orientation', 'mark': 0, 'options': ['Life Orientation']},
            {'subject': 'Elective 1', 'mark': '', 'options': [s for s in NSC_SUBJECTS if 'Language' not in s and s not in ['Mathematics', 'Mathematical Literacy', 'Life Orientation']]},
            {'subject': 'Elective 2', 'mark': '', 'options': [s for s in NSC_SUBJECTS if 'Language' not in s and s not in ['Mathematics', 'Mathematical Literacy', 'Life Orientation']]},
            {'subject': 'Elective 3', 'mark': '', 'options': [s for s in NSC_SUBJECTS if 'Language' not in s and s not in ['Mathematics', 'Mathematical Literacy', 'Life Orientation']]},
        ]

        for subject, mark in marks.items():
            if 'Home Language' in subject:
                marks_list[0]['subject'] = subject
                marks_list[0]['mark'] = mark
            elif 'First Additional Language' in subject:
                marks_list[1]['subject'] = subject
                marks_list[1]['mark'] = mark
            elif subject in ['Mathematics', 'Mathematical Literacy']:
                marks_list[2]['subject'] = subject
                marks_list[2]['mark'] = mark
            elif subject == 'Life Orientation':
                marks_list[3]['mark'] = 0
            else:
                for i in range(4, 7):
                    if marks_list[i]['mark'] == '':
                        marks_list[i]['subject'] = subject
                        marks_list[i]['mark'] = mark
                        break

        if marks and len(marks) < 7:
            messages.warning(request, f"You currently have {len(marks)} subjects. Please update your marks to include exactly 7 subjects as per NSC requirements.")

        if request.method == 'POST':
            if 'submit_marks' in request.POST:
                new_marks = {}
                subjects_entered = 0
                selected_subjects = set()

                for i in range(7):
                    if i == 3:  # Life Orientation
                        new_marks['Life Orientation'] = 0
                        subjects_entered += 1
                        selected_subjects.add('Life Orientation')
                        continue

                    subject = request.POST.get(f'subject_{i}')
                    mark = request.POST.get(f'mark_{i}')

                    if not subject or not mark:
                        messages.error(request, f"Missing subject or mark for entry {i+1}.")
                        logger.error(f"Missing subject/mark for entry {i+1}: subject={subject}, mark={mark}")
                        return redirect('helper:dashboard_student')

                    if subject not in NSC_SUBJECTS:
                        messages.error(request, f"Invalid subject: {subject}. Please select a valid NSC subject.")
                        logger.error(f"Invalid subject entered: {subject}")
                        return redirect('helper:dashboard_student')
                    if subject in selected_subjects:
                        messages.error(request, f"Duplicate subject: {subject}. Please select unique subjects.")
                        logger.error(f"Duplicate subject: {subject}")
                        return redirect('helper:dashboard_student')

                    try:
                        mark = int(mark.strip())
                        if not 0 <= mark <= 100:
                            messages.error(request, f"Mark for {subject} must be between 0 and 100.")
                            logger.error(f"Mark out of range for {subject}: {mark}")
                            return redirect('helper:dashboard_student')
                        new_marks[subject] = mark
                        subjects_entered += 1
                        selected_subjects.add(subject)
                    except (ValueError, TypeError):
                        messages.error(request, f"Invalid mark for {subject}. Please enter a number.")
                        logger.error(f"Invalid mark for {subject}: {mark}")
                        return redirect('helper:dashboard_student')

                if subjects_entered != 7:
                    messages.error(request, f"Please enter exactly 7 subjects. You entered {subjects_entered} subjects.")
                    logger.error(f"Incorrect number of subjects: {subjects_entered}")
                    return redirect('helper:dashboard_student')

                has_home_language = any('Home Language' in s for s in new_marks)
                has_fal = any('First Additional Language' in s for s in new_marks)
                has_math = any(s in ['Mathematics', 'Mathematical Literacy'] for s in new_marks)
                has_lo = 'Life Orientation' in new_marks

                if not (has_home_language and has_fal and has_math and has_lo):
                    messages.error(request, "You must include a Home Language, First Additional Language, Mathematics or Mathematical Literacy, and Life Orientation.")
                    logger.error("Missing required subjects: Home Language, FAL, Math, LO")
                    return redirect('helper:dashboard_student')

                student_profile.marks = new_marks
                aps_score = calculate_aps(new_marks)
                student_profile.stored_aps_score = aps_score
                student_profile.save()
                logger.debug(f"Marks updated and APS stored for user {request.user.username}: {student_profile.stored_aps_score}")
                if aps_score is None:
                    messages.warning(request, "APS score could not be calculated due to invalid marks.")
                else:
                    messages.success(request, f"Marks updated successfully! Your APS score is {aps_score}.")
                return redirect('helper:dashboard_student')
            else:
                # Handle document uploads, including proof of payment
                form = DocumentUploadForm(request.POST, request.FILES)
                if form.is_valid():
                    doc = form.save(commit=False)
                    doc.user = request.user
                    document_type = request.POST.get('document_type')
                    university_id = request.POST.get('university_id')
                    
                    if document_type == 'payment_proof' and university_id:
                        try:
                            university = University.objects.get(id=university_id)
                            doc.document_type = 'payment_proof'
                            doc.university = university
                            doc.save()
                            messages.success(request, f"Proof of payment for {university.name} uploaded successfully!")
                            logger.debug(f"Payment proof uploaded by {request.user.username} for {university.name}: {doc.file.name}")
                        except University.DoesNotExist:
                            messages.error(request, "Invalid university selected for payment proof.")
                            logger.error(f"Invalid university ID {university_id} for payment proof by {request.user.username}")
                            return redirect('helper:dashboard_student')
                    else:
                        doc.save()
                        messages.success(request, "Document uploaded successfully!")
                        logger.debug(f"Document uploaded by {request.user.username}: {doc.file.name}")
                    return redirect('helper:dashboard_student')
                messages.error(request, "Document upload failed. Please try again.")
                logger.error(f"Document upload failed for {request.user.username}: {form.errors}")
                return redirect('helper:dashboard_student')

        # Use stored APS score if available, otherwise calculate from marks
        student_aps = student_profile.stored_aps_score
        if student_aps is None and student_profile.marks:
            student_aps = calculate_aps(student_profile.marks)
            if student_aps is not None:
                student_profile.stored_aps_score = student_aps
                student_profile.save()
                logger.debug(f"Calculated and stored APS for {request.user.username}: {student_aps}")
            else:
                logger.warning(f"Failed to calculate APS for {request.user.username}: Invalid marks {student_profile.marks}")

        # Fetch university recommendations
        recommendations = []
        if student_aps is not None:
            try:
                eligible_universities = University.objects.filter(minimum_aps__lte=student_aps).order_by('name')[:5]
                recommendations = [
                    {
                        'id': uni.id,
                        'name': uni.name,
                        'description': uni.description or f"Explore opportunities at {uni.name}, known for its excellent programs.",
                        'due_date': UNIVERSITY_DUE_DATES.get(uni.name, "TBD"),
                        'application_fee': APPLICATION_FEES_2025.get(uni.name, "Not available")
                    } for uni in eligible_universities
                ]
                logger.debug(f"Fetched {len(recommendations)} recommendations for APS {student_aps}")
            except Exception as e:
                logger.error(f"Error fetching recommendations for {request.user.username}: {str(e)}", exc_info=True)
                messages.error(request, "Unable to fetch university recommendations at this time.")

        # Fetch qualified universities
        qualified_universities = []
        if student_aps is not None:
            try:
                qualified = University.objects.filter(minimum_aps__lte=student_aps).order_by('name')
                qualified_universities = [
                    {
                        'id': uni.id,
                        'name': uni.name,
                        'location': uni.province or "South Africa",
                        'due_date': UNIVERSITY_DUE_DATES.get(uni.name, "TBD"),
                        'application_fee': APPLICATION_FEES_2025.get(uni.name, "Not available")
                    } for uni in qualified
                ]
                logger.debug(f"Fetched {len(qualified_universities)} qualified universities for APS {student_aps}")
            except Exception as e:
                logger.error(f"Error fetching qualified universities for {request.user.username}: {str(e)}", exc_info=True)
                messages.error(request, "Unable to fetch qualified universities at this time.")

        context = {
            'form': form,
            'documents': documents,
            'selected_universities': selected_universities,
            'recommended_universities': recommendations,
            'universities': qualified_universities,
            'student_profile': student_profile,
            'marks_list': marks_list,
            'nsc_subjects': NSC_SUBJECTS,
            'UNIVERSITY_DUE_DATES': UNIVERSITY_DUE_DATES,
            'student_aps': student_aps,
        }
        return render(request, 'helper/dashboard_student.html', context)
    except Exception as e:
        logger.error(f"Error in dashboard_student view for {request.user.username}: {str(e)}", exc_info=True)
        messages.error(request, "An unexpected error occurred. Please try again later.")
        return render(request, 'helper/error.html', {'error': 'An unexpected error occurred'})

@login_required
def dashboard_guide(request):
    """Render the guide dashboard for non-student users."""
    return render(request, 'helper/dashboard_guide.html')

@login_required
def delete_document(request, doc_id):
    """Delete a user's uploaded document."""
    document = get_object_or_404(DocumentUpload, id=doc_id, user=request.user)
    if request.method == 'POST':
        document.delete()
        messages.success(request, "Document deleted successfully!")
        logger.debug(f"Document {doc_id} deleted by {request.user.username}")
    return redirect('helper:dashboard_student')

@login_required
def edit_document(request, doc_id):
    """Edit an existing document upload."""
    document = get_object_or_404(DocumentUpload, id=doc_id, user=request.user)
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            form.save()
            messages.success(request, "Document updated successfully!")
            logger.debug(f"Document {doc_id} updated by {request.user.username}")
            return redirect('helper:dashboard_student')
        messages.error(request, "Document update failed. Please try again.")
        logger.error(f"Document update failed for {request.user.username}: {form.errors}")
    return redirect('helper:dashboard_student')

@login_required
def universities_list(request):
    """Display and manage the list of universities for selection."""
    universities = University.objects.all().order_by('name')
    student_profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    student_aps = student_profile.stored_aps_score

    if request.method == 'POST':
        selected_ids = request.POST.getlist('universities')
        try:
            selected_universities = University.objects.filter(id__in=selected_ids)
            new_application_count = len(selected_universities)
            if not student_profile.can_apply() or new_application_count > student_profile.get_application_limit():
                upgrade_link = '<a href="/subscription/" class="text-primary">Upgrade your plan</a> to apply to more universities.'
                message = (
                    f"Your subscription package ({student_profile.get_subscription_package_display()}) allows only "
                    f"{student_profile.get_application_limit()} applications. You have already applied to "
                    f"{student_profile.application_count} universities. {upgrade_link}"
                )
                messages.error(request, mark_safe(message))
                return redirect('helper:universities_list')

            student_profile.selected_universities.set(selected_universities)
            student_profile.application_count = new_application_count
            student_profile.save()
            messages.success(request, "Selected universities updated successfully!")
            logger.debug(f"Selected universities updated for {request.user.username}: {new_application_count} universities")
        except Exception as e:
            logger.error(f"Error updating selected universities for {request.user.username}: {str(e)}", exc_info=True)
            messages.error(request, "An error occurred while updating selected universities.")
        return redirect('helper:universities_list')

    eligible_universities = universities.filter(minimum_aps__lte=student_aps) if student_aps else []
    selected_universities = student_profile.selected_universities.all()
    selected_with_details = [
        {
            'university': uni,
            'due_date': UNIVERSITY_DUE_DATES.get(uni.name, "TBD"),
            'faculties_open': FACULTIES_OPEN.get(uni.name, ["To be updated"]),
            'application_fee': APPLICATION_FEES_2025.get(uni.name, "Not available")
        } for uni in selected_universities
    ]
    universities_with_fees = [
        {
            'university': uni,
            'fee': APPLICATION_FEES_2025.get(uni.name, "Not available"),
            'due_date': UNIVERSITY_DUE_DATES.get(uni.name, "TBD")
        } if student_profile.can_access_fee_guidance() else {
            'university': uni,
            'fee': "Upgrade to Standard or higher to view fees",
            'due_date': UNIVERSITY_DUE_DATES.get(uni.name, "TBD")
        } for uni in eligible_universities
    ]

    total_university_fee = 0
    payment_breakdown = []

    for uni in selected_universities:
        fee_str = APPLICATION_FEES_2025.get(uni.name, "Not available")
        if "FREE" in fee_str:
            university_fee = 0
        elif "Not available" in fee_str:
            university_fee = 0
        else:
            fee_parts = fee_str.split(',')
            fee_value = fee_parts[0].strip()
            if '(' in fee_value:
                fee_value = fee_value.split('(')[0].strip()
            try:
                university_fee = int(fee_value.replace('R', ''))
            except (ValueError, AttributeError):
                university_fee = 0

        total_university_fee += university_fee
        payment_breakdown.append({
            'university': uni.name,
            'university_fee': university_fee,
        })

    package_costs = {
        'basic': 400,
        'standard': 600,
        'premium': 800,
        'ultimate': 1000,
    }
    package_cost = package_costs.get(student_profile.subscription_package, 0)

    total_payment = total_university_fee + package_cost

    return render(request, 'helper/universities_list.html', {
        'universities': universities_with_fees,
        'student_aps': student_aps,
        'eligible_universities': eligible_universities,
        'selected_universities': selected_with_details,
        'selected_university_objects': selected_universities,
        'APPLICATION_FEES_2025': APPLICATION_FEES_2025,
        'UNIVERSITY_DUE_DATES': UNIVERSITY_DUE_DATES,
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
    faculties_open = FACULTIES_OPEN.get(university.name, ["To be updated"])
    
    return render(request, 'helper/university_detail.html', {
        'university': university,
        'application_fee': application_fee,
        'due_date': due_date,
        'faculties_open': faculties_open,
        'student_profile': student_profile,
    })

@login_required
def university_faculties(request, uni_id):
    """Display available faculties and courses for a university."""
    university = get_object_or_404(University, id=uni_id)
    student_profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    faculties_open = FACULTIES_OPEN.get(university.name, ["To be updated"])
    faculty_courses = {faculty: FACULTY_COURSES.get(university.name, {}).get(faculty, ["No courses listed"])
                       for faculty in faculties_open}
    show_course_advice = student_profile.can_access_course_advice()
    return render(request, 'helper/university_faculties.html', {
        'university': university,
        'faculty_courses': faculty_courses,
        'show_course_advice': show_course_advice,
    })

@login_required
def pay_application_fee(request, uni_id):
    """Redirect to payment instructions for a single university application fee."""
    university = get_object_or_404(University, id=uni_id)
    return redirect('helper:pay_application_fee_instructions', uni_id=uni_id)

@login_required
def pay_application_fee_instructions(request, uni_id):
    """Display payment instructions for a single university application fee."""
    student_profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    university = get_object_or_404(University, id=uni_id)
    fee_str = APPLICATION_FEES_2025.get(university.name, "Not available")

    if "FREE" in fee_str:
        university_fee = 0
    elif "Not available" in fee_str:
        messages.error(request, f"Application fee for {university.name} is not available.")
        return redirect('helper:universities_list')
    else:
        fee_parts = fee_str.split(',')
        fee_value = fee_parts[0].strip()
        if '(' in fee_value:
            fee_value = fee_value.split('(')[0].strip()
        try:
            university_fee = int(fee_value.replace('R', ''))
        except (ValueError, AttributeError):
            messages.error(request, f"Unable to process application fee for {university.name}.")
            return redirect('helper:universities_list')

    total_fee = university_fee

    bank_details = {
        "bank_name": "TBD Bank",
        "account_number": "1234567890",
        "account_holder": "Varsity Plug (Pty) Ltd",
        "branch_code": "123456",
        "reference": f"APPFEE-{request.user.username}-{university.name.replace(' ', '-')}"
    }

    return render(request, 'helper/pay_application_fee_instructions.html', {
        'university': university,
        'university_fee': university_fee,
        'total_fee': total_fee,
        'bank_details': bank_details,
    })

@login_required
def pay_all_application_fees(request):
    """Display payment instructions for all selected universities' application fees."""
    student_profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    selected_universities = student_profile.selected_universities.all()

    if not selected_universities:
        messages.error(request, "You have not selected any universities to apply to.")
        return redirect('helper:universities_list')

    total_university_fee = 0
    payment_breakdown = []

    for uni in selected_universities:
        fee_str = APPLICATION_FEES_2025.get(uni.name, "Not available")
        if "FREE" in fee_str:
            university_fee = 0
        elif "Not available" in fee_str:
            university_fee = 0
        else:
            fee_parts = fee_str.split(',')
            fee_value = fee_parts[0].strip()
            if '(' in fee_value:
                fee_value = fee_value.split('(')[0].strip()
            try:
                university_fee = int(fee_value.replace('R', ''))
            except (ValueError, AttributeError):
                university_fee = 0

        total_university_fee += university_fee
        payment_breakdown.append({
            'university': uni.name,
            'university_fee': university_fee,
        })

    package_costs = {
        'basic': 400,
        'standard': 600,
        'premium': 800,
        'ultimate': 1000,
    }
    package_cost = package_costs.get(student_profile.subscription_package, 0)

    total_payment = total_university_fee + package_cost

    if total_payment == 0:
        messages.info(request, "No payment is required for your selected universities at this time.")
        return redirect('helper:universities_list')

    university_names = "-".join(uni.name.replace(' ', '-') for uni in selected_universities)
    bank_details = {
        "bank_name": "TBD Bank",
        "account_number": "1234567890",
        "account_holder": "Varsity Plug (Pty) Ltd",
        "branch_code": "123456",
        "reference": f"BULK-APPFEE-{request.user.username}-{university_names}"
    }

    return render(request, 'helper/pay_all_application_fees.html', {
        'selected_universities': selected_universities,
        'payment_breakdown': payment_breakdown,
        'total_university_fee': total_university_fee,
        'package_cost': package_cost,
        'total_payment': total_payment,
        'bank_details': bank_details,
    })

@login_required
@ratelimit(key='user', rate='10/m', method='POST')
def ai_chat(request):
    """Handle AI chat requests for user queries."""
    if request.method != 'POST':
        logger.error("Invalid request method for ai_chat")
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        if not user_message:
            logger.debug("Empty message received in ai_chat")
            return JsonResponse({'error': 'Message cannot be empty'}, status=400)

        system_prompt = (
            "You are a helpful assistant for the Varsity Plug app, designed to assist students in navigating the app and clarifying questions about university applications in South Africa. "
            "Provide clear, concise, and accurate answers. Do not provide harmful, illegal, or inappropriate content. "
            "Focus on topics related to the app's features, such as uploading documents, selecting universities, calculating fees, and understanding admission requirements. "
            "If a question is outside the app's scope, politely redirect the user to contact support or their university."
        )

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            max_tokens=150,
            temperature=0.7,
        )

        ai_response = response.choices[0].message['content'].strip()
        logger.debug(f"AI chat response for {request.user.username}: {ai_response}")
        return JsonResponse({'response': ai_response}, status=200)

    except json.JSONDecodeError:
        logger.error("Invalid JSON in ai_chat request")
        return JsonResponse({'error': 'Invalid request format'}, status=400)
    except openai.error.AuthenticationError:
        logger.error("OpenAI API authentication error")
        return JsonResponse({'error': 'Invalid API key. Please contact the administrator.'}, status=500)
    except openai.error.RateLimitError:
        logger.error("OpenAI API rate limit exceeded")
        return JsonResponse({'error': 'Rate limit exceeded. Please try again later.'}, status=429)
    except Exception as e:
        logger.error(f"Error in ai_chat: {str(e)}", exc_info=True)
        return JsonResponse({'error': 'An error occurred. Please try again.'}, status=500)

@login_required
def select_university(request, uni_id):
    """Handle AJAX-based university selection."""
    university = get_object_or_404(University, id=uni_id)
    student_profile = get_object_or_404(StudentProfile, user=request.user)

    if not student_profile.can_apply():
        return JsonResponse({
            'success': False,
            'message': f"Your subscription package ({student_profile.get_subscription_package_display()}) has reached its application limit."
        }, status=403)

    if student_profile.application_count >= student_profile.get_application_limit():
        upgrade_link = '<a href="/subscription/" class="text-primary">Upgrade your plan</a> to apply to more universities.'
        return JsonResponse({
            'success': False,
            'message': f"Your subscription allows only {student_profile.get_application_limit()} applications. {upgrade_link}"
        }, status=403)

    if university in student_profile.selected_universities.all():
        return JsonResponse({
            'success': False,
            'message': f"{university.name} is already selected."
        }, status=400)

    try:
        student_profile.selected_universities.add(university)
        student_profile.application_count += 1
        student_profile.save()
        logger.info(f"University {university.name} selected by {request.user.username}. Application count: {student_profile.application_count}")
        return JsonResponse({
            'success': True,
            'message': f"{university.name} has been successfully selected!",
            'application_count': student_profile.application_count
        }, status=200)
    except Exception as e:
        logger.error(f"Error selecting university {university.name} for {request.user.username}: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': "An error occurred while selecting the university. Please try again."
        }, status=500)