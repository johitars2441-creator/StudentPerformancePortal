from django import forms
from .models import Marks


class MarksForm(forms.ModelForm):

    class Meta:
        model = Marks
        fields = [
            'student',
            'subject',
            'exam_type',
            'marks_obtained',
            'exam_date',
        ]

        widgets = {
            'exam_date': forms.DateInput(
                attrs={'type': 'date'}
            ),
        }

    def clean(self):
        cleaned_data = super().clean()

        student = cleaned_data.get('student')
        subject = cleaned_data.get('subject')
        exam_type = cleaned_data.get('exam_type')
        marks_obtained = cleaned_data.get('marks_obtained')

        if subject and marks_obtained is not None:
            if marks_obtained > subject.max_marks:
                self.add_error(
                    'marks_obtained',
                    f'Marks cannot exceed {subject.max_marks}.'
                )

        # One record per student, subject, and assessment type.
        if student and subject and exam_type:
            duplicate = Marks.objects.filter(
                student=student,
                subject=subject,
                exam_type=exam_type,
            )

            if self.instance.pk:
                duplicate = duplicate.exclude(pk=self.instance.pk)

            if duplicate.exists():
                self.add_error(
                    'exam_type',
                    'Marks for this student, subject, and assessment '
                    'type have already been recorded.'
                )

        return cleaned_data

    def save(self, commit=True):
        marks = super().save(commit=False)
        marks.max_marks = marks.subject.max_marks

        if commit:
            marks.save()

        return marks