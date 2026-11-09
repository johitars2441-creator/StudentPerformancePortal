from django.db import models
from django.contrib.auth.models import User
from batches.models import Batch
from subjects.models import Subject
from students.models import Student


class MockInterview(models.Model):
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('COMPLETED', 'Completed'),
        ('ABSENT', 'Candidate Absent'),
        ('CANCELLED', 'Cancelled'),
    ]

    PLATFORM_CHOICES = [
        ('GOOGLE_MEET', 'Google Meet'),
        ('ZOOM', 'Zoom'),
        ('OTHER', 'Other / Direct Link'),
    ]

    batch = models.ForeignKey(
        Batch,
        on_delete=models.CASCADE,
        related_name='mock_interviews'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='mock_interviews'
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='mock_interviews'
    )
    staff = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='conducted_interviews'
    )

    scheduled_datetime = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=30)
    meeting_platform = models.CharField(
        max_length=30,
        choices=PLATFORM_CHOICES,
        default='GOOGLE_MEET'
    )
    meeting_url = models.URLField(
        max_length=500,
        help_text="Google Meet or Zoom Link"
    )
    instructions = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='SCHEDULED'
    )
    email_sent = models.BooleanField(default=False)

    # Evaluation fields
    marks_obtained = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    max_marks = models.PositiveIntegerField(default=50)
    technical_rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Scale 1 to 10"
    )
    communication_rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Scale 1 to 10"
    )
    problem_solving_rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Scale 1 to 10"
    )
    feedback_notes = models.TextField(blank=True)
    strengths = models.TextField(blank=True)
    areas_for_improvement = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-scheduled_datetime']

    def __str__(self):
        return f"{self.student.roll_number} - {self.subject.subject_name} Mock Interview ({self.status})"

    @property
    def percentage(self):
        if not self.marks_obtained or not self.max_marks:
            return 0.0
        return round((float(self.marks_obtained) / self.max_marks) * 100, 2)
