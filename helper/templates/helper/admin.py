# helper/admin.py
from django.contrib import admin
from .models import DocumentUpload, StudentProfile, University

admin.site.register(DocumentUpload)
admin.site.register(StudentProfile)
admin.site.register(University)