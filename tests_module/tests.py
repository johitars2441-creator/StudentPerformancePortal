from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from accounts.models import UserProfile, StaffProfile
from batches.models import Batch, BatchStaffAssignment
from students.models import Student
from subjects.models import Subject
from tests_module.models import Test, MCQQuestion, CodingQuestion, TestAttempt
from mock_interviews.models import MockInterview
from analytics.pdf_generator import generate_student_pdf_report
from tests_module.services import generate_mcqs_with_ai, evaluate_student_code_with_ai


class SystemIntegrationTestCase(TestCase):
    def setUp(self):
        # 1. Super Admin
        self.admin_user = User.objects.create_superuser('admin_user', 'admin@portal.edu', 'pass123')
        self.admin_profile = UserProfile.objects.create(user=self.admin_user, role='SUPER_ADMIN')

        # 2. Staff User
        self.staff_user = User.objects.create_user('prof_smith', 'smith@portal.edu', 'pass123')
        self.staff_profile = UserProfile.objects.create(user=self.staff_user, role='STAFF')
        self.staff_details = StaffProfile.objects.create(user_profile=self.staff_profile, staff_id='STF-01')

        # 3. Batches
        self.batch_a = Batch.objects.create(batch_code='BATCH-CS-2026', batch_name='Computer Science Cohort')
        self.batch_b = Batch.objects.create(batch_code='BATCH-AI-2026', batch_name='AI Cohort')

        # Assign staff to batch A only
        BatchStaffAssignment.objects.create(batch=self.batch_a, staff=self.staff_user)

        # 4. Student enrolled in Batch A
        self.student_user = User.objects.create_user('alice', 'alice@student.edu', 'pass123')
        self.student_profile = UserProfile.objects.create(user=self.student_user, role='STUDENT')
        self.student = Student.objects.create(
            user=self.student_user,
            batch=self.batch_a,
            roll_number='CS-001',
            full_name='Alice Smith',
            email='alice@student.edu',
            admission_date=timezone.now().date()
        )

        # 5. Subject
        self.subject = Subject.objects.create(subject_code='CS101', subject_name='Python Programming')
        self.subject.batches.add(self.batch_a)

    def test_batch_uniqueness(self):
        """Batch codes must be strictly unique."""
        from django.db import IntegrityError
        with self.assertRaises(Exception):
            Batch.objects.create(batch_code='BATCH-CS-2026', batch_name='Duplicate Batch')

    def test_staff_batch_scoping(self):
        """Staff should only access their assigned batches."""
        from accounts.decorators import can_access_batch
        self.assertTrue(can_access_batch(self.staff_user, self.batch_a))
        self.assertFalse(can_access_batch(self.staff_user, self.batch_b))
        self.assertTrue(can_access_batch(self.admin_user, self.batch_b))

    def test_ai_question_generation_and_scoring(self):
        """Verify AI question generation and code evaluation services."""
        mcqs = generate_mcqs_with_ai("Python lists, dictionaries and functions", num_questions=2, total_marks=20)
        self.assertEqual(len(mcqs), 2)

        code_eval = evaluate_student_code_with_ai(
            problem_statement="Reverse a string in python",
            student_code="def reverse_str(s):\n    return s[::-1]",
            language="python",
            max_marks=50
        )
        self.assertIn("marks_awarded", code_eval)
        self.assertGreater(code_eval["marks_awarded"], 0)

    def test_one_warning_proctoring_protocol(self):
        """Verify tab-switch 1 warning policy and auto-termination on 2nd switch."""
        test = Test.objects.create(
            batch=self.batch_a,
            subject=self.subject,
            test_type='MCQ',
            title='Proctoring Test',
            total_marks=20,
            duration_minutes=15,
            is_published=True
        )
        attempt = TestAttempt.objects.create(test=test, student=self.student, status='IN_PROGRESS')

        client = Client()
        client.force_login(self.student_user)

        # Switch 1: Should give warning, not force submit
        res1 = client.post(f'/tests/attempt/{attempt.id}/tab-switch/')
        data1 = res1.json()
        self.assertEqual(data1['tab_switch_count'], 1)
        self.assertFalse(data1['force_submit'])

        # Switch 2: Should trigger force submission
        res2 = client.post(f'/tests/attempt/{attempt.id}/tab-switch/')
        data2 = res2.json()
        self.assertEqual(data2['tab_switch_count'], 2)
        self.assertTrue(data2['force_submit'])

        attempt.refresh_from_db()
        self.assertEqual(attempt.status, 'FORCE_SUBMITTED')

    def test_mock_interview_and_pdf_generation(self):
        """Verify mock interview model and PDF report generator."""
        interview = MockInterview.objects.create(
            batch=self.batch_a,
            subject=self.subject,
            student=self.student,
            staff=self.staff_user,
            scheduled_datetime=timezone.now(),
            meeting_url='https://meet.google.com/abc-defg-hij',
            status='COMPLETED',
            marks_obtained=45.0,
            max_marks=50
        )
        self.assertEqual(interview.percentage, 90.0)

        pdf_buffer = generate_student_pdf_report(self.student)
        pdf_bytes = pdf_buffer.getvalue()
        self.assertTrue(len(pdf_bytes) > 1000)
        self.assertTrue(pdf_bytes.startswith(b'%PDF'))
