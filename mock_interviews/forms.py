from django import forms
from mock_interviews.models import MockInterview
from batches.models import Batch, BatchStaffAssignment
from subjects.models import Subject
from students.models import Student


class MockInterviewScheduleForm(forms.ModelForm):
    class Meta:
        model = MockInterview
        fields = [
            'batch', 'subject', 'student', 'scheduled_datetime',
            'duration_minutes', 'meeting_platform', 'meeting_url', 'instructions'
        ]
        widgets = {
            'batch': forms.Select(attrs={'class': 'form-select', 'id': 'batchSelect'}),
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'student': forms.Select(attrs={'class': 'form-select'}),
            'scheduled_datetime': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'meeting_platform': forms.Select(attrs={'class': 'form-select'}),
            'meeting_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://meet.google.com/xxx-yyyy-zzz or Zoom URL'}),
            'instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Topics covered, prerequisites, or preparation notes'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and not user.is_superuser:
            assigned_ids = BatchStaffAssignment.objects.filter(staff=user).values_list('batch_id', flat=True)
            self.fields['batch'].queryset = Batch.objects.filter(id__in=assigned_ids)
            self.fields['student'].queryset = Student.objects.filter(batch_id__in=assigned_ids)


class MockInterviewEvaluationForm(forms.ModelForm):
    class Meta:
        model = MockInterview
        fields = [
            'marks_obtained', 'max_marks', 'status',
            'technical_rating', 'communication_rating', 'problem_solving_rating',
            'feedback_notes', 'strengths', 'areas_for_improvement'
        ]
        widgets = {
            'marks_obtained': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5'}),
            'max_marks': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'technical_rating': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10}),
            'communication_rating': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10}),
            'problem_solving_rating': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10}),
            'feedback_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Overall candidate evaluation'}),
            'strengths': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Core strengths demonstrated'}),
            'areas_for_improvement': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Constructive feedback & topics to revisit'}),
        }
