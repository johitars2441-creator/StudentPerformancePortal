from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from batches.models import Batch, BatchStaffAssignment
from accounts.models import UserProfile, StaffProfile
from students.models import Student


class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = ['batch_code', 'batch_name', 'description', 'start_date', 'end_date', 'is_active']
        widgets = {
            'batch_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. BATCH-2026-CS01'}),
            'batch_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Computer Science 2026'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_batch_code(self):
        code = self.cleaned_data['batch_code'].strip().upper()
        # Check uniqueness excluding self if editing
        qs = Batch.objects.filter(batch_code__iexact=code)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(f"Batch code '{code}' already exists. Batch codes must be unique.")
        return code


class StaffCreationForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Temporary Password'}))
    first_name = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}))
    staff_id = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Staff ID / Employee Code'}))
    department = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Department'}))
    designation = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Designation'}))

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError(f"Username '{username}' is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError(f"Email '{email}' is already in use.")
        return email


class StudentEnrollmentForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Student Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Initial Password'}))
    full_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}))
    roll_number = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Roll Number (e.g. CS2026-001)'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Student Email'}))
    department = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Department (e.g. Computer Science)'}))
    admission_date = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError(f"Username '{username}' already exists.")
        return username

    def clean_roll_number(self):
        roll = self.cleaned_data['roll_number'].strip().upper()
        if Student.objects.filter(roll_number__iexact=roll).exists():
            raise ValidationError(f"Roll number '{roll}' is already assigned to another student.")
        return roll

    def clean_email(self):
        email = self.cleaned_data['email'].strip()
        if Student.objects.filter(email__iexact=email).exists():
            raise ValidationError(f"Email '{email}' is already registered for a student.")
        return email

