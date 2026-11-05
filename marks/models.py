from django.db import models
from students.models import Student
from subjects.models import Subject


class Marks(models.Model):

    EXAM_CHOICES = [
        ('CODING_TEST', 'Coding Test'),
        ('MCQ', 'MCQ'),
        ('MOCK_INTERVIEW', 'Mock Interview'),
    ]
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='marks'
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='marks'
    )

    exam_type = models.CharField(
        max_length=20,
        choices=EXAM_CHOICES
    )

    marks_obtained = models.PositiveIntegerField()

    max_marks = models.PositiveIntegerField(default=100)

    exam_date = models.DateField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'subject', 'exam_type'],
                name='unique_student_subject_exam'
            )
        ]

    def __str__(self):
        return (
            f"{self.student.full_name} - "
            f"{self.subject.subject_name} - "
            f"{self.exam_type}"
        )

    @property
    def percentage(self):
        if self.max_marks == 0:
            return 0
        return round(
            (self.marks_obtained / self.max_marks) * 100,
            2
        )

    @property
    def grade(self):
        percentage = self.percentage

        if percentage >= 90:
            return 'A+'
        elif percentage >= 80:
            return 'A'
        elif percentage >= 70:
            return 'B'
        elif percentage >= 60:
            return 'C'
        elif percentage >= 40:
            return 'D'
        else:
            return 'F'