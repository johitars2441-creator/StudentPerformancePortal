import json
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden
from django.db import transaction
from django.contrib.auth.models import User

from students.models import Student
from subjects.models import Subject
from marks.models import Marks
from attendance.models import Attendance
from accounts.models import UserProfile
from batches.models import Batch
from tests_module.models import TestAttempt, Test
from mock_interviews.models import MockInterview
from .forms import StudentCreationForm


REQUIRED_EXAMS = [
    'CODING_TEST',
    'MCQ',
    'MOCK_INTERVIEW',
]


def calculate_grade(percentage):
    if percentage is None:
        return None
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
    return 'F'


@login_required
def student_dashboard(request):
    try:
        student = Student.objects.select_related('batch').get(user=request.user)
    except Student.DoesNotExist:
        return render(
            request,
            'students/dashboard.html',
            {'error': 'Your student profile has not been initialized yet. Please contact your instructor.'}
        )

    # Filter subjects for the student's batch if available
    if student.batch:
        batch_subjects = student.batch.subjects.all()
        subjects = list(batch_subjects) if batch_subjects.exists() else list(Subject.objects.all())
    else:
        subjects = list(Subject.objects.all())

    # Fetch all attempts and mock interviews
    test_attempts = TestAttempt.objects.filter(
        student=student,
        status__in=['SUBMITTED', 'TIMED_OUT', 'FORCE_SUBMITTED']
    ).select_related('test__subject')

    mock_interviews = MockInterview.objects.filter(
        student=student,
        status='COMPLETED'
    ).select_related('subject', 'staff')

    # Subject-wise 3-tier performance calculation
    subject_performance = []
    radar_labels = []
    radar_student_scores = []
    radar_batch_scores = []
    bar_coding_scores = []
    bar_mcq_scores = []
    bar_interview_scores = []

    all_subject_averages = []

    for sub in subjects:
        # 1. Coding score
        coding_att = test_attempts.filter(test__subject=sub, test__test_type='CODING').first()
        legacy_coding = Marks.objects.filter(student=student, subject=sub, exam_type='CODING_TEST').first()
        coding_pct = coding_att.percentage if coding_att else (legacy_coding.percentage if legacy_coding else None)

        # 2. MCQ score
        mcq_att = test_attempts.filter(test__subject=sub, test__test_type='MCQ').first()
        legacy_mcq = Marks.objects.filter(student=student, subject=sub, exam_type='MCQ').first()
        mcq_pct = mcq_att.percentage if mcq_att else (legacy_mcq.percentage if legacy_mcq else None)

        # 3. Mock Interview score
        interview = mock_interviews.filter(subject=sub).first()
        legacy_int = Marks.objects.filter(student=student, subject=sub, exam_type='MOCK_INTERVIEW').first()
        int_pct = interview.percentage if interview else (legacy_int.percentage if legacy_int else None)

        scores = [s for s in [coding_pct, mcq_pct, int_pct] if s is not None]
        sub_avg = round(sum(scores) / len(scores), 1) if scores else None
        if sub_avg is not None:
            all_subject_averages.append(sub_avg)

        # Compute batch average for this subject
        batch_avg = 72.0  # reasonable baseline
        if student.batch:
            other_atts = TestAttempt.objects.filter(
                test__batch=student.batch,
                test__subject=sub,
                status__in=['SUBMITTED', 'TIMED_OUT']
            )
            if other_atts.exists():
                batch_avg = round(sum(a.percentage for a in other_atts) / other_atts.count(), 1)

        is_complete = (coding_pct is not None and mcq_pct is not None and int_pct is not None)

        subject_performance.append({
            'subject_name': sub.subject_name,
            'coding_pct': coding_pct,
            'mcq_pct': mcq_pct,
            'int_pct': int_pct,
            'average': sub_avg,
            'grade': calculate_grade(sub_avg),
            'is_complete': is_complete
        })

        radar_labels.append(sub.subject_name)
        radar_student_scores.append(sub_avg or 0)
        radar_batch_scores.append(batch_avg)

        bar_coding_scores.append(coding_pct or 0)
        bar_mcq_scores.append(mcq_pct or 0)
        bar_interview_scores.append(int_pct or 0)

    # Overall Student Average
    overall_average = round(sum(all_subject_averages) / len(all_subject_averages), 1) if all_subject_averages else None
    overall_grade = calculate_grade(overall_average)

    # Ranking calculation in cohort
    batch_students = Student.objects.filter(batch=student.batch) if student.batch else Student.objects.all()
    total_batch_students = batch_students.count()

    student_rank = 1
    if overall_average is not None:
        for other in batch_students:
            if other.id != student.id:
                other_atts = TestAttempt.objects.filter(student=other, status__in=['SUBMITTED', 'TIMED_OUT'])
                if other_atts.exists():
                    other_avg = sum(a.percentage for a in other_atts) / other_atts.count()
                    if other_avg > overall_average:
                        student_rank += 1

    # Timeline of past attempts
    timeline_labels = []
    timeline_scores = []
    recent_attempts = test_attempts.order_by('submit_time')[:10]
    for att in recent_attempts:
        timeline_labels.append(att.test.title[:15])
        timeline_scores.append(att.percentage)

    # Attendance
    attendance_records = Attendance.objects.filter(student=student)
    total_att = attendance_records.count()
    attended = attendance_records.filter(status__in=['PRESENT', 'LATE']).count()
    attendance_pct = round(attended / total_att * 100, 1) if total_att else 100.0

    # Package Chart JSON safely
    chart_payload = {
        'radar_labels': radar_labels,
        'radar_student_scores': radar_student_scores,
        'radar_batch_scores': radar_batch_scores,
        'bar_coding_scores': bar_coding_scores,
        'bar_mcq_scores': bar_mcq_scores,
        'bar_interview_scores': bar_interview_scores,
        'timeline_labels': timeline_labels if timeline_labels else ['Test 1', 'Test 2'],
        'timeline_scores': timeline_scores if timeline_scores else [0, 0]
    }

    context = {
        'student': student,
        'subject_performance': subject_performance,
        'overall_average': overall_average,
        'overall_grade': overall_grade,
        'student_rank': student_rank,
        'total_batch_students': total_batch_students,
        'attendance_percentage': attendance_pct,
        'recent_attempts': test_attempts.order_by('-submit_time')[:5],
        'recent_interviews': mock_interviews[:5],
        'chart_data_json': json.dumps(chart_payload),
    }

    return render(request, 'students/dashboard.html', context)


@login_required
def manage_students(request):
    """
    Redirects staff/admin to the batch management interface where students are managed by cohort.
    """
    from accounts.decorators import get_user_role
    role = get_user_role(request.user)
    if role not in ['SUPER_ADMIN', 'STAFF']:
        return HttpResponseForbidden("You do not have permission to access this page.")
    return redirect('batches:batch_list')

