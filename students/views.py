
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Student
from subjects.models import Subject
from marks.models import Marks
from attendance.models import Attendance
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden

from accounts.models import UserProfile
from .forms import StudentCreationForm


REQUIRED_EXAMS = [
    'CODING_TEST',
    'MCQ',
    'MOCK_INTERVIEW',
]


def calculate_grade(percentage):
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



def calculate_performance(student, subjects):

    subject_percentages = []
    all_subjects_complete = bool(subjects)

    for subject in subjects:

        records = Marks.objects.filter(
            student=student,
            subject=subject,
            exam_type__in=REQUIRED_EXAMS
        )

        recorded_exams = set(
            records.values_list('exam_type', flat=True)
        )

        if not all(
            exam in recorded_exams for exam in REQUIRED_EXAMS
        ):
            all_subjects_complete = False

        percentages = [
            mark.percentage for mark in records
        ]

        if percentages:
            subject_average = (
                sum(percentages) / len(percentages)
            )
            subject_percentages.append(subject_average)

    if not subject_percentages:
        return None, None, False

    overall_average = round(
        sum(subject_percentages) / len(subject_percentages),
        2
    )

    passed = all(
        percentage >= 40
        for percentage in subject_percentages
    )

    return overall_average, passed, all_subjects_complete


@login_required
def student_dashboard(request):

    try:
        student = Student.objects.get(user=request.user)

    except Student.DoesNotExist:
        return render(
            request,
            'students/dashboard.html',
            {'error': 'Your student profile has not been created.'}
        )

    subjects = list(Subject.objects.all())

    marks = Marks.objects.filter(
        student=student
    ).select_related('subject')

    # Current average, pass status and completion
    average_marks, passed, is_complete = (
        calculate_performance(student, subjects)
    )

    # Subject-wise performance
    subject_performance = []

    for subject in subjects:

        subject_marks = marks.filter(
            subject=subject,
            exam_type__in=REQUIRED_EXAMS
        )

        percentages = [
            mark.percentage for mark in subject_marks
        ]

        recorded_exams = set(
            subject_marks.values_list('exam_type', flat=True)
        )

        subject_complete = all(
            exam in recorded_exams
            for exam in REQUIRED_EXAMS
        )

        subject_average = (
            round(sum(percentages) / len(percentages), 2)
            if percentages else None
        )

        subject_performance.append({
            'subject_name': subject.subject_name,
            'average': subject_average,
            'grade': (
                calculate_grade(subject_average)
                if subject_average is not None else None
            ),
            'assessment_count': subject_marks.count(),
            'is_complete': subject_complete,
        })

    # Calculate provisional or final rankings
    rankings = []

    for other_student in Student.objects.all():

        other_average, _, _ = calculate_performance(
            other_student, subjects
        )

        if other_average is not None:
            rankings.append({
                'student_id': other_student.id,
                'average': other_average
            })

    rankings.sort(
        key=lambda item: item['average'],
        reverse=True
    )

    student_rank = None
    previous_average = None
    current_rank = None

    for position, item in enumerate(rankings, start=1):

        if item['average'] != previous_average:
            current_rank = position

        if item['student_id'] == student.id:
            student_rank = current_rank
            break

        previous_average = item['average']

    # Attendance
    attendance_records = Attendance.objects.filter(
        student=student
    )

    total_attendance = attendance_records.count()

    attended = attendance_records.filter(
        status__in=['PRESENT', 'LATE']
    ).count()

    attendance_percentage = (
        round(attended / total_attendance * 100, 2)
        if total_attendance else 0
    )

    # Result status
    if average_marks is None:
        result_status = 'No Marks Yet'

    elif not is_complete:
        result_status = (
            'Provisional Pass'
            if passed else 'Provisional Fail'
        )

    else:
        result_status = 'Pass' if passed else 'Fail'

    context = {
        'student': student,
        'marks': marks,
        'total_assessments': marks.count(),
        'average_marks': average_marks,
        'overall_grade': (
            calculate_grade(average_marks)
            if average_marks is not None else None
        ),
        'passed': passed,
        'result_status': result_status,
        'is_complete': is_complete,
        'student_rank': student_rank,
        'attendance_percentage': attendance_percentage,
        'subject_performance': subject_performance,
    }

    return render(
        request,
        'students/dashboard.html',
        context
    )

@login_required
def manage_students(request):
    # Only superusers or users with the ADMIN role can access this page.
    profile = getattr(request.user, "userprofile", None)

    if not (
        request.user.is_superuser
        or (profile and profile.role == "ADMIN")
    ):
        return HttpResponseForbidden(
            "You do not have permission to access this page."
        )

    if request.method == "POST":
        form = StudentCreationForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                user = User.objects.create_user(
                    username=form.cleaned_data["username"],
                    email=form.cleaned_data["email"],
                    password=form.cleaned_data["password"],
                )

                UserProfile.objects.create(
                    user=user,
                    role="STUDENT",
                )

                Student.objects.create(
                    user=user,
                    full_name=form.cleaned_data["full_name"],
                    email=form.cleaned_data["email"],
                    roll_number=form.cleaned_data["roll_number"],
                    department=form.cleaned_data["department"],
                    admission_date=form.cleaned_data["admission_date"],
                )

            return redirect("manage_students")
    else:
        form = StudentCreationForm()

    students = Student.objects.select_related("user").order_by(
        "roll_number"
    )

    return render(
        request,
        "students/manage_students.html",
        {
            "form": form,
            "students": students,
        },
    )
