from django import forms
from django.contrib.auth.models import User


class StudentCreationForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(
        widget=forms.PasswordInput()
    )
    full_name = forms.CharField(max_length=100)
    email = forms.EmailField()
    roll_number = forms.CharField(max_length=20)
    department = forms.CharField(max_length=100)
    admission_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"})
    )

    def clean_username(self):
        username = self.cleaned_data["username"]

        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(
                "This username already exists."
            )

        return username

    def clean_email(self):
        email = self.cleaned_data["email"]

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                "This email already belongs to a user."
            )

        return email