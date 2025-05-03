from django import forms
from .models import DocumentUpload
import logging

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
            valid_extensions = ['.pdf', '.jpg', '.png']
            extension = '.' + file.name.split('.')[-1].lower()
            if extension not in valid_extensions:
                raise forms.ValidationError(
                    'Invalid file type. Only PDF, JPG, and PNG files are allowed.'
                )
            max_size = 5 * 1024 * 1024  # 5MB in bytes
            if file.size > max_size:
                raise forms.ValidationError(
                    'File size exceeds 5MB. Please upload a smaller file.'
                )
        return file

class MarksForm(forms.Form):
    subject_0 = forms.ChoiceField(
        choices=[(s, s) for s in [
            "Afrikaans Home Language", "English Home Language", "IsiNdebele Home Language",
            "IsiXhosa Home Language", "IsiZulu Home Language", "Sepedi Home Language",
            "Sesotho Home Language", "Setswana Home Language", "Siswati Home Language",
            "Tshivenda Home Language", "Xitsonga Home Language"
        ]],
        label="Home Language"
    )
    mark_0 = forms.IntegerField(min_value=0, max_value=100, label="Home Language Mark")
    subject_1 = forms.ChoiceField(
        choices=[(s, s) for s in [
            "Afrikaans First Additional Language", "English First Additional Language",
            "IsiNdebele First Additional Language", "IsiXhosa First Additional Language",
            "IsiZulu First Additional Language", "Sepedi First Additional Language",
            "Sesotho First Additional Language", "Setswana First Additional Language",
            "Siswati First Additional Language", "Tshivenda First Additional Language",
            "Xitsonga First Additional Language"
        ]],
        label="First Additional Language"
    )
    mark_1 = forms.IntegerField(min_value=0, max_value=100, label="First Additional Language Mark")
    subject_2 = forms.ChoiceField(
        choices=[('Mathematics', 'Mathematics'), ('Mathematical Literacy', 'Mathematical Literacy')],
        label="Mathematics or Mathematical Literacy"
    )
    mark_2 = forms.IntegerField(min_value=0, max_value=100, label="Mathematics/Math Literacy Mark")
    subject_3 = forms.CharField(initial='Life Orientation', widget=forms.HiddenInput())
    mark_3 = forms.IntegerField(initial=0, widget=forms.HiddenInput())
    subject_4 = forms.ChoiceField(
        choices=[(s, s) for s in [
            "Accounting", "Agricultural Sciences", "Business Studies", "Computer Applications Technology",
            "Consumer Studies", "Dramatic Arts", "Economics", "Engineering Graphics and Design",
            "Geography", "History", "Information Technology", "Life Sciences", "Music",
            "Physical Sciences", "Religion Studies", "Tourism", "Visual Arts"
        ]],
        label="Elective 1"
    )
    mark_4 = forms.IntegerField(min_value=0, max_value=100, label="Elective 1 Mark")
    subject_5 = forms.ChoiceField(
        choices=[(s, s) for s in [
            "Accounting", "Agricultural Sciences", "Business Studies", "Computer Applications Technology",
            "Consumer Studies", "Dramatic Arts", "Economics", "Engineering Graphics and Design",
            "Geography", "History", "Information Technology", "Life Sciences", "Music",
            "Physical Sciences", "Religion Studies", "Tourism", "Visual Arts"
        ]],
        label="Elective 2"
    )
    mark_5 = forms.IntegerField(min_value=0, max_value=100, label="Elective 2 Mark")
    subject_6 = forms.ChoiceField(
        choices=[(s, s) for s in [
            "Accounting", "Agricultural Sciences", "Business Studies", "Computer Applications Technology",
            "Consumer Studies", "Dramatic Arts", "Economics", "Engineering Graphics and Design",
            "Geography", "History", "Information Technology", "Life Sciences", "Music",
            "Physical Sciences", "Religion Studies", "Tourism", "Visual Arts"
        ]],
        label="Elective 3"
    )
    mark_6 = forms.IntegerField(min_value=0, max_value=100, label="Elective 3 Mark")

    def clean(self):
        cleaned_data = super().clean()
        subjects = [cleaned_data.get(f'subject_{i}') for i in range(7)]
        marks = [cleaned_data.get(f'mark_{i}') for i in range(7)]
        logger = logging.getLogger('helper')
        logger.debug(f"MarksForm cleaned data: {cleaned_data}")

        if None in subjects:
            raise forms.ValidationError("All subject fields are required.")
        if len(set(subjects)) != 7:
            raise forms.ValidationError("All subjects must be unique.")
        if not any('Home Language' in s for s in subjects):
            raise forms.ValidationError("A Home Language subject is required.")
        if not any('First Additional Language' in s for s in subjects):
            raise forms.ValidationError("A First Additional Language subject is required.")
        if not any(s in ['Mathematics', 'Mathematical Literacy'] for s in subjects):
            raise forms.ValidationError("Mathematics or Mathematical Literacy is required.")
        if 'Life Orientation' not in subjects:
            raise forms.ValidationError("Life Orientation is required.")
        for i, mark in enumerate(marks):
            if mark is None:
                raise forms.ValidationError(f"Mark for {subjects[i]} is required.")
            if not 0 <= mark <= 100:
                raise forms.ValidationError(f"Mark for {subjects[i]} must be between 0 and 100.")

        return cleaned_data