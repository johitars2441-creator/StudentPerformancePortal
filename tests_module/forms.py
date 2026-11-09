from django import forms
from tests_module.models import Test
from batches.models import Batch
from subjects.models import Subject


class TestCreationForm(forms.ModelForm):
    num_questions = forms.IntegerField(
        initial=5,
        min_value=1,
        max_value=30,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text="Number of questions for MCQ test"
    )
    generate_with_ai = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Check to automatically generate questions using Google Gemini AI from the uploaded document"
    )

    class Meta:
        model = Test
        fields = [
            'batch', 'subject', 'test_type', 'title', 'description',
            'total_marks', 'duration_minutes', 'start_window', 'end_window',
            'source_file', 'is_published'
        ]
        widgets = {
            'batch': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'test_type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Unit 1 Assessment'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional instructions for students'}),
            'total_marks': forms.NumberInput(attrs={'class': 'form-control'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'start_window': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_window': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'source_file': forms.FileInput(attrs={'class': 'form-control'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and not user.is_superuser:
            # Filter batches to assigned batches
            from batches.models import BatchStaffAssignment
            assigned_ids = BatchStaffAssignment.objects.filter(staff=user).values_list('batch_id', flat=True)
            self.fields['batch'].queryset = Batch.objects.filter(id__in=assigned_ids)
