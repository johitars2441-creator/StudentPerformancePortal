from django import forms
from .models import Attendance


class AttendanceForm(forms.ModelForm):

    class Meta:
        model = Attendance
        fields = [
            'student',
            'date',
            'status',
            'remarks',
        ]

        widgets = {
            'date': forms.DateInput(
                attrs={'type': 'date'}
            ),
            'remarks': forms.Textarea(
                attrs={'rows': 2}
            ),
        }