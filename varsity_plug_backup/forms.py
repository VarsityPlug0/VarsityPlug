class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'university', 'course', 'year_of_study', 'proof_of_payment']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'university': forms.TextInput(attrs={'class': 'form-control'}),
            'course': forms.TextInput(attrs={'class': 'form-control'}),
            'year_of_study': forms.NumberInput(attrs={'class': 'form-control'}),
            'proof_of_payment': forms.FileInput(attrs={'class': 'form-control'}),
        } 