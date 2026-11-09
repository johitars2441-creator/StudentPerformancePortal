from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from mock_interviews.models import MockInterview
from mock_interviews.forms import MockInterviewScheduleForm, MockInterviewEvaluationForm
from mock_interviews.services import send_mock_interview_invitation_email
from batches.models import Batch, BatchStaffAssignment
from accounts.decorators import (
    staff_required,
    student_required,
    get_user_role,
    can_access_batch
)


@login_required
@staff_required
def interview_list(request):
    role = get_user_role(request.user)
    if role == 'SUPER_ADMIN':
        interviews = MockInterview.objects.all().select_related('batch', 'subject', 'student', 'staff')
    else:
        assigned_batch_ids = BatchStaffAssignment.objects.filter(staff=request.user).values_list('batch_id', flat=True)
        interviews = MockInterview.objects.filter(batch_id__in=assigned_batch_ids).select_related('batch', 'subject', 'student', 'staff')

    return render(request, 'mock_interviews/interview_list.html', {
        'interviews': interviews,
        'is_admin': role == 'SUPER_ADMIN',
    })


@login_required
@staff_required
def schedule_interview(request):
    if request.method == 'POST':
        form = MockInterviewScheduleForm(request.POST, user=request.user)
        if form.is_valid():
            interview = form.save(commit=False)
            interview.staff = request.user
            interview.save()

            # Dispatch invitation email with Google Meet / Zoom link
            email_sent = send_mock_interview_invitation_email(interview)
            if email_sent:
                messages.success(request, f"Mock interview scheduled and email invite dispatched to {interview.student.email}!")
            else:
                messages.success(request, f"Mock interview scheduled for {interview.student.full_name}.")

            return redirect('mock_interviews:interview_list')
    else:
        form = MockInterviewScheduleForm(user=request.user)

    return render(request, 'mock_interviews/schedule_form.html', {
        'form': form,
    })


@login_required
@staff_required
def evaluate_interview(request, interview_id):
    interview = get_object_or_404(MockInterview, id=interview_id)
    if not can_access_batch(request.user, interview.batch):
        messages.error(request, "Permission denied for this student's batch.")
        return redirect('mock_interviews:interview_list')

    if request.method == 'POST':
        form = MockInterviewEvaluationForm(request.POST, instance=interview)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.completed_at = timezone.now()
            obj.save()
            messages.success(request, f"Evaluation and feedback recorded for {interview.student.full_name}!")
            return redirect('mock_interviews:interview_list')
    else:
        form = MockInterviewEvaluationForm(instance=interview)

    return render(request, 'mock_interviews/evaluate_form.html', {
        'form': form,
        'interview': interview,
    })


@login_required
@student_required
def student_mock_interviews(request):
    student = getattr(request.user, 'student', None)
    if not student:
        messages.warning(request, "No student profile found.")
        return redirect('/')

    interviews = MockInterview.objects.filter(student=student).select_related('subject', 'staff')

    return render(request, 'mock_interviews/student_interviews.html', {
        'interviews': interviews,
        'student': student,
    })
