from django.shortcuts import render
from django.db.models import Avg, Count, Q
from django.http import JsonResponse
from subjects.models import Subject
from marks.models import Marks
from students.models import Student
from attendance.models import Attendance
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render
from accounts.models import UserProfile


def overview(request):
    total_students = Student.objects.count()

    total_assessments = Marks.objects.count()

    total_attendance_records = Attendance.objects.count()

    average_percentage = 0

    percentages = []

    for mark in Marks.objects.all():
        percentages.append(mark.percentage)

    if percentages:
        average_percentage = round(
            sum(percentages) / len(percentages), 2
        )

    data = {
        'total_students': total_students,
        'total_assessments': total_assessments,
        'total_attendance_records': total_attendance_records,
        'average_percentage': average_percentage,
    }

    return JsonResponse(data)


REQUIRED_ASSESSMENTS = {
    'CODING_TEST',
    'MCQ',
    'MOCK_INTERVIEW',
}


def results(request):
    students = Student.objects.all()
    subjects = list(Subject.objects.all())

    student_results = []

    for student in students:
        subject_results = []
        complete = bool(subjects)

        for subject in subjects:
            records = list(
                Marks.objects.filter(
                    student=student,
                    subject=subject
                )
            )

            completed_types = {
                record.exam_type for record in records
            }

            if not REQUIRED_ASSESSMENTS.issubset(completed_types):
                complete = False

            if records:
                subject_percentage = sum(
                    record.percentage for record in records
                ) / len(records)

                subject_results.append({
                    'subject': subject.subject_name,
                    'percentage': round(subject_percentage, 2),
                })

        if not complete or len(subject_results) != len(subjects):
            student_results.append({
                'student': student.full_name,
                'roll_number': student.roll_number,
                'status': 'Incomplete',
                'average_percentage': None,
                'grade': None,
                'rank': None,
                'subjects': subject_results,
            })
            continue

        average = sum(
            item['percentage'] for item in subject_results
        ) / len(subject_results)

        passed = all(
            item['percentage'] >= 40
            for item in subject_results
        )

        if average >= 90:
            grade = 'A+'
        elif average >= 80:
            grade = 'A'
        elif average >= 70:
            grade = 'B'
        elif average >= 60:
            grade = 'C'
        elif average >= 40:
            grade = 'D'
        else:
            grade = 'F'

        student_results.append({
            'student': student.full_name,
            'roll_number': student.roll_number,
            'status': 'Pass' if passed else 'Fail',
            'average_percentage': round(average, 2),
            'grade': grade,
            'rank': None,
            'subjects': subject_results,
        })

    eligible = [
        item for item in student_results
        if item['status'] in ('Pass', 'Fail')
    ]

    eligible.sort(
        key=lambda item: item['average_percentage'],
        reverse=True
    )

    # Students with equal averages receive the same rank.
    previous_average = None
    current_rank = 0

    for position, item in enumerate(eligible, start=1):
        if item['average_percentage'] != previous_average:
            current_rank = position

        item['rank'] = current_rank
        previous_average = item['average_percentage']

    pass_count = sum(
        item['status'] == 'Pass' for item in eligible
    )

    fail_count = sum(
        item['status'] == 'Fail' for item in eligible
    )

    incomplete_count = sum(
        item['status'] == 'Incomplete'
        for item in student_results
    )

    return JsonResponse({
        'total_students': len(student_results),
        'passed': pass_count,
        'failed': fail_count,
        'incomplete': incomplete_count,
        'rankings': eligible,
        'incomplete_students': [
            item for item in student_results
            if item['status'] == 'Incomplete'
        ],
    })





@login_required
def dashboard(request):
    # Step 1: Check whether the user is an admin
    profile = getattr(request.user, "userprofile", None)

    is_admin = (
        request.user.is_superuser
        or (profile and profile.role == "ADMIN")
    )

    if not is_admin:
        return HttpResponseForbidden(
            "You do not have permission to access the admin dashboard."
        )

    # Step 2: Calculate dashboard summary values
    total_students = Student.objects.count()
    total_subjects = Subject.objects.count()
    total_assessments = Marks.objects.count()
    total_attendance = Attendance.objects.count()

    # Step 3: Calculate average percentage
    all_marks = list(Marks.objects.all())

    average_percentage = (
        round(
            sum(mark.percentage for mark in all_marks)
            / len(all_marks),
            2,
        )
        if all_marks
        else 0
    )

    # Step 4: Count assessment records by grade
    grade_distribution = {
        "A+": 0,
        "A": 0,
        "B": 0,
        "C": 0,
        "D": 0,
        "F": 0,
    }

    for mark in all_marks:
        grade_distribution[mark.grade] += 1

    # Step 5: Calculate average percentage for each subject
    subject_labels = []
    subject_averages = []

    for subject in Subject.objects.all():
        subject_marks = [
            mark for mark in all_marks
            if mark.subject_id == subject.id
        ]

        if subject_marks:
            subject_average = sum(
                mark.percentage for mark in subject_marks
            ) / len(subject_marks)
        else:
            subject_average = 0

        subject_labels.append(subject.subject_name)
        subject_averages.append(round(subject_average, 2))

    # Step 6: Send data to the HTML page
    context = {
        "total_students": total_students,
        "total_subjects": total_subjects,
        "total_assessments": total_assessments,
        "total_attendance": total_attendance,
        "average_percentage": average_percentage,
        "grade_distribution": grade_distribution,
        "subject_labels": subject_labels,
        "subject_averages": subject_averages,
    }

    return render(request, "analytics/dashboard.html", context)



def attendance_analytics(request):
    total_records = Attendance.objects.count()

    present_count = Attendance.objects.filter(
        status='PRESENT'
    ).count()

    absent_count = Attendance.objects.filter(
        status='ABSENT'
    ).count()

    late_count = Attendance.objects.filter(
        status='LATE'
    ).count()

    attendance_percentage = 0

    if total_records > 0:
        attendance_percentage = round(
            (present_count / total_records) * 100, 2
        )

    data = {
        'total_records': total_records,
        'present': present_count,
        'absent': absent_count,
        'late': late_count,
        'attendance_percentage': attendance_percentage,
    }

    return JsonResponse(data)

def subject_performance(request):
    subjects = Subject.objects.all()
    result = []

    for subject in subjects:
        subject_marks = Marks.objects.filter(
            subject=subject
        )

        percentages = [
            mark.percentage for mark in subject_marks
        ]

        average = 0

        if percentages:
            average = round(
                sum(percentages) / len(percentages), 2
            )

        result.append({
            'subject_code': subject.subject_code,
            'subject_name': subject.subject_name,
            'average_percentage': average,
            'total_assessments': len(percentages),
        })

    return JsonResponse({'subjects': result})


REPORT_REQUIRED_EXAMS = [
    'MOCK_INTERVIEW',
    'MCQ',
    'CODING_TEST',
]


def report_grade(percentage):
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
def student_analytics_report(request):
    # Only admins and superusers can view student reports.
    profile = getattr(request.user, 'userprofile', None)

    if not (
        request.user.is_superuser
        or (profile and profile.role == 'ADMIN')
    ):
        return HttpResponseForbidden(
            'You do not have permission to access this report.'
        )

    students = Student.objects.order_by('roll_number')

    # Read the selected student from the URL.
    selected_id = request.GET.get('student_id')
    selected_student = None

    if selected_id:
        selected_student = students.filter(
            pk=selected_id
        ).first()

    # If no student was selected, show the first student.
    if selected_student is None:
        selected_student = students.first()

    if selected_student is None:
        return render(
            request,
            'analytics/student_report.html',
            {
                'students': students,
                'no_students': True,
            }
        )

    subjects = list(Subject.objects.order_by('subject_name'))

    marks = Marks.objects.filter(
        student=selected_student
    ).select_related('subject').order_by(
        'subject__subject_name', 'exam_date'
    )

    subject_reports = []
    subject_averages = []
    all_subjects_complete = bool(subjects)

    for subject in subjects:
        subject_marks = list(
            marks.filter(subject=subject)
        )

        required_marks = [
            mark for mark in subject_marks
            if mark.exam_type in REPORT_REQUIRED_EXAMS
        ]

        recorded_exams = {
            mark.exam_type for mark in required_marks
        }

        complete = all(
            exam in recorded_exams
            for exam in REPORT_REQUIRED_EXAMS
        )

        if not complete:
            all_subjects_complete = False

        percentages = [
            mark.percentage for mark in required_marks
        ]

        average = (
            round(sum(percentages) / len(percentages), 2)
            if percentages else None
        )

        if average is not None:
            subject_averages.append(average)

        subject_reports.append({
            'subject': subject,
            'marks': subject_marks,
            'assessment_count': len(required_marks),
            'average': average,
            'grade': (
                report_grade(average)
                if average is not None else None
            ),
            'complete': complete,
            'pending_exams': [
                exam for exam in REPORT_REQUIRED_EXAMS
                if exam not in recorded_exams
            ],
        })

    overall_average = (
        round(sum(subject_averages) / len(subject_averages), 2)
        if subject_averages else None
    )

    passed = (
        all(average >= 40 for average in subject_averages)
        if subject_averages else None
    )

    if overall_average is None:
        result_status = 'No Marks Yet'
    elif not all_subjects_complete:
        result_status = (
            'Provisional Pass' if passed
            else 'Provisional Fail'
        )
    else:
        result_status = 'Pass' if passed else 'Fail'

    # Attendance report
    attendance_records = Attendance.objects.filter(
        student=selected_student
    )

    total_attendance = attendance_records.count()

    attended = attendance_records.filter(
        status__in=['PRESENT', 'LATE']
    ).count()

    attendance_percentage = (
        round(attended / total_attendance * 100, 2)
        if total_attendance else 0
    )

    # Final class rank: only students with complete assessments.
    final_rank = None
    eligible_students = []

    if all_subjects_complete and overall_average is not None:
        for other_student in students:
            other_marks = Marks.objects.filter(
                student=other_student
            ).select_related('subject')

            other_subject_averages = []
            other_complete = bool(subjects)

            for subject in subjects:
                subject_records = list(
                    other_marks.filter(
                        subject=subject,
                        exam_type__in=REPORT_REQUIRED_EXAMS
                    )
                )

                recorded = {
                    mark.exam_type for mark in subject_records
                }

                if not all(
                    exam in recorded
                    for exam in REPORT_REQUIRED_EXAMS
                ):
                    other_complete = False
                    break

                other_subject_averages.append(
                    sum(mark.percentage for mark in subject_records)
                    / len(subject_records)
                )

            if other_complete and other_subject_averages:
                eligible_students.append({
                    'id': other_student.id,
                    'average': round(
                        sum(other_subject_averages)
                        / len(other_subject_averages), 2
                    ),
                })

        eligible_students.sort(
            key=lambda item: item['average'],
            reverse=True
        )

        previous_average = None
        rank = None

        for position, item in enumerate(
            eligible_students, start=1
        ):
            if item['average'] != previous_average:
                rank = position

            if item['id'] == selected_student.id:
                final_rank = rank
                break

            previous_average = item['average']

    context = {
        'students': students,
        'selected_student': selected_student,
        'subject_reports': subject_reports,
        'total_assessments': marks.count(),
        'overall_average': overall_average,
        'overall_grade': (
            report_grade(overall_average)
            if overall_average is not None else None
        ),
        'result_status': result_status,
        'is_complete': all_subjects_complete,
        'attendance_percentage': attendance_percentage,
        'total_attendance': total_attendance,
        'final_rank': final_rank,
        'required_exams': REPORT_REQUIRED_EXAMS,
    }

    return render(
        request,
        'analytics/student_report.html',
        context
    )


from django.http import FileResponse
from .pdf_generator import generate_student_pdf_report
from accounts.decorators import get_user_role, can_access_batch
from django.shortcuts import get_object_or_404


@login_required
def download_student_pdf(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    role = get_user_role(request.user)

    if role == 'STUDENT':
        if not hasattr(request.user, 'student') or request.user.student.id != student.id:
            return HttpResponseForbidden("You can only download your own performance transcript.")
    elif role == 'STAFF':
        if student.batch and not can_access_batch(request.user, student.batch):
            return HttpResponseForbidden("Permission denied for this batch.")

    buffer = generate_student_pdf_report(student)
    filename = f"Performance_Card_{student.roll_number}.pdf"
    return FileResponse(buffer, as_attachment=True, filename=filename, content_type='application/pdf')

