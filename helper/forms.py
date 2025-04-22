from django import forms
from .models import DocumentUpload

class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = DocumentUpload
        fields = ['document_type', 'file']
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.png'}),
        }

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Validate file type
            valid_extensions = ['.pdf', '.jpg', '.png']
            extension = '.' + file.name.split('.')[-1].lower()
            if extension not in valid_extensions:
                raise forms.ValidationError(
                    'Invalid file type. Only PDF, JPG, and PNG files are allowed.'
                )

            # Validate file size (max 5MB)
            max_size = 5 * 1024 * 1024  # 5MB in bytes
            if file.size > max_size:
                raise forms.ValidationError(
                    'File size exceeds 5MB. Please upload a smaller file.'
                )

        return file