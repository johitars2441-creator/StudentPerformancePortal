from django.db import models
from django.contrib.auth.models import User
from batches.models import Batch
from subjects.models import Subject
from students.models import Student


class Test(models.Model):
    TEST_TYPE_CHOICES = [
        ('MCQ', 'MCQ Test'),
        ('CODING', 'Coding Test'),
    ]

    batch = models.ForeignKey(
        Batch,
        on_delete=models.CASCADE,
        related_name='tests'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='tests'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tests_created'
    )
    test_type = models.CharField(max_length=20, choices=TEST_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    total_marks = models.PositiveIntegerField(default=100)
    duration_minutes = models.PositiveIntegerField(
        default=30,
        help_text="Allowed time in minutes"
    )
    start_window = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Active window start datetime"
    )
    end_window = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Active window deadline datetime"
    )
    is_published = models.BooleanField(default=False)
    source_file = models.FileField(upload_to='test_docs/%Y/%m/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.batch.batch_code}] {self.subject.subject_name} - {self.title} ({self.get_test_type_display()})"


class MCQQuestion(models.Model):
    OPTION_CHOICES = [
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
    ]

    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE,
        related_name='mcq_questions'
    )
    question_text = models.TextField()
    option_a = models.TextField()
    option_b = models.TextField()
    option_c = models.TextField()
    option_d = models.TextField()
    correct_option = models.CharField(max_length=1, choices=OPTION_CHOICES)
    explanation = models.TextField(blank=True)
    marks = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"Q{self.id}: {self.question_text[:50]}..."


class CodingQuestion(models.Model):
    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE,
        related_name='coding_questions'
    )
    title = models.CharField(max_length=200)
    problem_statement = models.TextField()
    constraints = models.TextField(blank=True)
    input_format = models.TextField(blank=True)
    output_format = models.TextField(blank=True)
    sample_input = models.TextField(blank=True)
    sample_output = models.TextField(blank=True)
    sample_explanation = models.TextField(blank=True)
    marks = models.PositiveIntegerField(default=50)

    def __str__(self):
        return f"Coding: {self.title}"


class TestAttempt(models.Model):
    STATUS_CHOICES = [
        ('NOT_ATTENDED', 'Not Attended'),
        ('IN_PROGRESS', 'In Progress'),
        ('SUBMITTED', 'Submitted'),
        ('FORCE_SUBMITTED', 'Terminated (Tab Switch Violation)'),
        ('TIMED_OUT', 'Auto-Submitted (Timeout)'),
        ('ABSENT', 'Absent'),
    ]

    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE,
        related_name='attempts'
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='test_attempts'
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='NOT_ATTENDED'
    )
    start_time = models.DateTimeField(null=True, blank=True)
    submit_time = models.DateTimeField(null=True, blank=True)
    tab_switch_count = models.PositiveIntegerField(default=0)
    warning_shown = models.BooleanField(default=False)
    total_score = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    max_marks = models.PositiveIntegerField(default=100)
    ai_feedback_summary = models.TextField(blank=True)
    is_evaluated = models.BooleanField(default=False)

    class Meta:
        unique_together = ('test', 'student')
        ordering = ['-submit_time']

    def __str__(self):
        return f"{self.student.roll_number} - {self.test.title} ({self.status})"

    @property
    def percentage(self):
        if not self.max_marks:
            return 0.0
        return round((float(self.total_score) / self.max_marks) * 100, 2)


class MCQAnswerSubmission(models.Model):
    attempt = models.ForeignKey(
        TestAttempt,
        on_delete=models.CASCADE,
        related_name='mcq_answers'
    )
    question = models.ForeignKey(
        MCQQuestion,
        on_delete=models.CASCADE
    )
    selected_option = models.CharField(max_length=1, blank=True)
    is_correct = models.BooleanField(default=False)
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.attempt.student.roll_number} - Q{self.question_id}: {self.selected_option}"


class CodingAnswerSubmission(models.Model):
    attempt = models.ForeignKey(
        TestAttempt,
        on_delete=models.CASCADE,
        related_name='coding_answers'
    )
    question = models.ForeignKey(
        CodingQuestion,
        on_delete=models.CASCADE
    )
    submitted_code = models.TextField(blank=True)
    programming_language = models.CharField(max_length=30, default='python')
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    ai_correctness_notes = models.TextField(blank=True)
    ai_code_quality_notes = models.TextField(blank=True)
    ai_edge_case_notes = models.TextField(blank=True)
    ai_complexity_notes = models.TextField(blank=True)
    ai_suggestions = models.TextField(blank=True)

    def __str__(self):
        return f"{self.attempt.student.roll_number} - Coding Solution ({self.marks_obtained}/{self.question.marks})"
