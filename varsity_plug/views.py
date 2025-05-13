from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import University, Document, Subscription, UserProfile
from django.core.files.storage import FileSystemStorage
import json

@login_required
def dashboard(request):
    # Get or create user profile
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Get user's subscription
    subscription, created = Subscription.objects.get_or_create(user=request.user)
    
    # Get user's documents
    documents = Document.objects.filter(user=request.user).order_by('-uploaded_at')
    
    # Get qualified universities based on APS score
    qualified_universities = user_profile.get_qualified_universities()
    
    context = {
        'user_profile': user_profile,
        'subscription': subscription,
        'documents': documents,
        'recommendations': qualified_universities,
        'qualified_universities_count': qualified_universities.count(),
        'subscription_status': f"{subscription.get_subscription_type_display()} Subscription",
        'has_active_subscription': subscription.is_active,
    }
    
    return render(request, 'varsity_plug/dashboard.html', context)

@login_required
def upload_document(request):
    if request.method == 'POST':
        document_type = request.POST.get('document_type')
        document_file = request.FILES.get('document_file')
        
        if document_file and document_type:
            # Validate file size (5MB limit)
            if document_file.size > 5 * 1024 * 1024:
                messages.error(request, 'File size must be less than 5MB')
                return redirect('dashboard')
            
            # Validate file type
            allowed_types = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png']
            if document_file.content_type not in allowed_types:
                messages.error(request, 'Invalid file type. Please upload PDF, JPG, JPEG, or PNG files only.')
                return redirect('dashboard')
            
            # Create document
            Document.objects.create(
                user=request.user,
                document_type=document_type,
                file=document_file
            )
            messages.success(request, 'Document uploaded successfully')
        else:
            messages.error(request, 'Please provide both document type and file')
    
    return redirect('dashboard')

@login_required
def delete_document(request, document_id):
    document = get_object_or_404(Document, id=document_id, user=request.user)
    document.delete()
    messages.success(request, 'Document deleted successfully')
    return redirect('dashboard')

@login_required
def update_aps_score(request):
    if request.method == 'POST':
        try:
            aps_score = int(request.POST.get('aps_score'))
            if 0 <= aps_score <= 100:
                user_profile, created = UserProfile.objects.get_or_create(user=request.user)
                user_profile.aps_score = aps_score
                user_profile.save()
                messages.success(request, 'APS score updated successfully')
            else:
                messages.error(request, 'APS score must be between 0 and 100')
        except (ValueError, TypeError):
            messages.error(request, 'Invalid APS score')
    
    return redirect('dashboard')

@login_required
def varsity_assistant(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')
            
            # Here you would typically integrate with your chatbot/assistant service
            # For now, we'll just echo the message back
            response = {
                'message': f'I received your message: {user_message}'
            }
            return JsonResponse(response)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405) 