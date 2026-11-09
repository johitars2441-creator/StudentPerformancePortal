from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from django.db import transaction

from tests_module.models import (
    Test,
    MCQQuestion,
    CodingQuestion,
    TestAttempt,
    MCQAnswerSubmission,
    CodingAnswerSubmission
)
from tests_module.forms import TestCreationForm
from tests_module.services import (
    extract_text_from_file,
    generate_mcqs_with_ai,
    generate_coding_challenge_with_ai,
    evaluate_student_code_with_ai
)
from batches.models import Batch, BatchStaffAssignment
from students.models import Student
from accounts.decorators import (
    staff_required,
    student_required,
    get_user_role,
    can_access_batch
)


@login_required
@staff_required
def test_list(request):
    role = get_user_role(request.user)
    if role == 'SUPER_ADMIN':
        tests = Test.objects.all().select_related('batch', 'subject', 'created_by')
    else:
        assigned_batch_ids = BatchStaffAssignment.objects.filter(staff=request.user).values_list('batch_id', flat=True)
        tests = Test.objects.filter(batch_id__in=assigned_batch_ids).select_related('batch', 'subject', 'created_by')

    return render(request, 'tests_module/test_list.html', {
        'tests': tests,
        'is_admin': role == 'SUPER_ADMIN',
    })


@login_required
@staff_required
def create_test(request):
    if request.method == 'POST':
        form = TestCreationForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            test = form.save(commit=False)
            test.created_by = request.user
            test.save()

            generate_ai = form.cleaned_data.get('generate_with_ai')
            source_file = request.FILES.get('source_file')
            doc_text = ""
            if source_file:
                doc_text = extract_text_from_file(source_file)

            if generate_ai:
                if test.test_type == 'MCQ':
                    num_q = form.cleaned_data.get('num_questions') or 5
                    mcqs = generate_mcqs_with_ai(
                        document_text=doc_text,
                        num_questions=num_q,
                        subject_name=test.subject.subject_name,
                        total_marks=test.total_marks
                    )
                    for item in mcqs:
                        MCQQuestion.objects.create(
                            test=test,
                            question_text=item.get('question_text', ''),
                            option_a=item.get('option_a', ''),
                            option_b=item.get('option_b', ''),
                            option_c=item.get('option_c', ''),
                            option_d=item.get('option_d', ''),
                            correct_option=item.get('correct_option', 'A'),
                            explanation=item.get('explanation', ''),
                            marks=item.get('marks', 1)
                        )
                    messages.success(request, f"AI successfully generated {len(mcqs)} MCQ questions from your document!")

                elif test.test_type == 'CODING':
                    code_data = generate_coding_challenge_with_ai(
                        document_text=doc_text,
                        subject_name=test.subject.subject_name,
                        total_marks=test.total_marks
                    )
                    CodingQuestion.objects.create(
                        test=test,
                        title=code_data.get('title', f"{test.subject.subject_name} Challenge"),
                        problem_statement=code_data.get('problem_statement', ''),
                        constraints=code_data.get('constraints', ''),
                        input_format=code_data.get('input_format', ''),
                        output_format=code_data.get('output_format', ''),
                        sample_input=code_data.get('sample_input', ''),
                        sample_output=code_data.get('sample_output', ''),
                        sample_explanation=code_data.get('sample_explanation', ''),
                        marks=test.total_marks
                    )
                    messages.success(request, "AI successfully generated coding problem and constraints from your document!")

            return redirect('tests_module:test_detail', test_id=test.id)
    else:
        form = TestCreationForm(user=request.user)

    return render(request, 'tests_module/create_test.html', {
        'form': form,
    })


@login_required
@staff_required
def test_detail(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    if not can_access_batch(request.user, test.batch):
        messages.error(request, "Permission denied for this batch's test.")
        return redirect('tests_module:test_list')

    attempts = test.attempts.select_related('student').order_by('-total_score')
    mcq_questions = test.mcq_questions.all()
    coding_questions = test.coding_questions.all()

    return render(request, 'tests_module/test_detail.html', {
        'test': test,
        'attempts': attempts,
        'mcq_questions': mcq_questions,
        'coding_questions': coding_questions,
    })


@login_required
@staff_required
def toggle_publish(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    if not can_access_batch(request.user, test.batch):
        return HttpResponseForbidden()

    test.is_published = not test.is_published
    test.save()
    status_str = "Published to students" if test.is_published else "Unpublished (Draft)"
    messages.success(request, f"Test status changed to: {status_str}")
    return redirect('tests_module:test_detail', test_id=test.id)


# ==========================================
# STUDENT TEST-TAKING & PROCTORING VIEWS
# ==========================================

@login_required
@student_required
def student_test_portal(request):
    """
    Displays tests available for the logged-in student's batch.
    """
    student = getattr(request.user, 'student', None)
    if not student or not student.batch:
        messages.warning(request, "You are not assigned to an active batch. Please contact staff.")
        return render(request, 'tests_module/student_tests.html', {'tests': []})

    tests = Test.objects.filter(batch=student.batch, is_published=True).select_related('subject')
    
    # Map each test to student's attempt status
    attempts = {a.test_id: a for a in TestAttempt.objects.filter(student=student)}
    now = timezone.now()

    test_cards = []
    for t in tests:
        attempt = attempts.get(t.id)
        is_open = True
        if t.start_window and now < t.start_window:
            is_open = False
        if t.end_window and now > t.end_window:
            is_open = False
            # Check if student was absent
            if not attempt:
                attempt = TestAttempt.objects.create(
                    test=t,
                    student=student,
                    status='ABSENT',
                    max_marks=t.total_marks
                )

        test_cards.append({
            'test': t,
            'attempt': attempt,
            'is_open': is_open,
        })

    return render(request, 'tests_module/student_tests.html', {
        'student': student,
        'test_cards': test_cards,
    })


@login_required
@student_required
def take_test(request, test_id):
    student = getattr(request.user, 'student', None)
    test = get_object_or_404(Test, id=test_id, is_published=True)

    if not student or test.batch_id != student.batch_id:
        messages.error(request, "You are not enrolled in this test's batch.")
        return redirect('tests_module:student_portal')

    attempt, created = TestAttempt.objects.get_or_create(
        test=test,
        student=student,
        defaults={
            'status': 'IN_PROGRESS',
            'start_time': timezone.now(),
            'max_marks': test.total_marks,
        }
    )

    if attempt.status in ['SUBMITTED', 'FORCE_SUBMITTED', 'TIMED_OUT']:
        messages.info(request, "You have already completed or submitted this test.")
        return redirect('tests_module:test_result', attempt_id=attempt.id)

    if attempt.status == 'ABSENT':
        messages.error(request, "This test deadline has passed and is marked as Absent.")
        return redirect('tests_module:student_portal')

    # If re-entering in-progress test
    if attempt.status == 'NOT_ATTENDED':
        attempt.status = 'IN_PROGRESS'
        attempt.start_time = timezone.now()
        attempt.save()

    mcq_questions = test.mcq_questions.all()
    coding_question = test.coding_questions.first()

    return render(request, 'tests_module/exam_room.html', {
        'test': test,
        'attempt': attempt,
        'mcq_questions': mcq_questions,
        'coding_question': coding_question,
        'duration_seconds': test.duration_minutes * 60,
    })


@login_required
def log_tab_switch(request, attempt_id):
    """
    API endpoint: invoked via fetch() when tab switch or window blur is detected.
    Enforces the 1-Warning Policy:
    Violation 1: Returns warning_count = 1, force_submit = False.
    Violation 2: Returns warning_count = 2, force_submit = True (triggering instant auto-submit).
    """
    attempt = get_object_or_404(TestAttempt, id=attempt_id)
    if attempt.status not in ['IN_PROGRESS', 'NOT_ATTENDED']:
        return JsonResponse({'status': 'already_finished', 'force_submit': True})

    attempt.tab_switch_count += 1
    force_submit = attempt.tab_switch_count >= 2

    if force_submit:
        attempt.status = 'FORCE_SUBMITTED'
        attempt.submit_time = timezone.now()
        attempt.save()

    attempt.save()

    return JsonResponse({
        'tab_switch_count': attempt.tab_switch_count,
        'warning_limit': 1,
        'force_submit': force_submit,
        'message': "Final warning: next violation will immediately terminate your exam." if attempt.tab_switch_count == 1 else "Exam terminated due to repeated tab switching."
    })


@login_required
def submit_test(request, attempt_id):
    """
    Handles student submission (Normal submit, timeout auto-submit, or tab-switch force submit).
    Performs automated AI evaluation:
    - MCQs evaluated deterministically + scored.
    - Coding solutions evaluated via Google Gemini API.
    """
    attempt = get_object_or_404(TestAttempt, id=attempt_id)
    test = attempt.test
    submission_reason = request.POST.get('submission_reason', 'NORMAL')

    with transaction.atomic():
        if submission_reason == 'FORCE_SUBMITTED':
            attempt.status = 'FORCE_SUBMITTED'
        elif submission_reason == 'TIMED_OUT':
            attempt.status = 'TIMED_OUT'
        else:
            attempt.status = 'SUBMITTED'

        attempt.submit_time = timezone.now()
        total_score = 0.0

        if test.test_type == 'MCQ':
            # Evaluate MCQs
            for q in test.mcq_questions.all():
                selected = request.POST.get(f'question_{q.id}', '').strip().upper()
                is_correct = (selected == q.correct_option)
                marks_earned = float(q.marks) if is_correct else 0.0
                total_score += marks_earned

                MCQAnswerSubmission.objects.update_or_create(
                    attempt=attempt,
                    question=q,
                    defaults={
                        'selected_option': selected,
                        'is_correct': is_correct,
                        'marks_obtained': marks_earned
                    }
                )

            attempt.total_score = total_score
            attempt.is_evaluated = True

        elif test.test_type == 'CODING':
            coding_q = test.coding_questions.first()
            if coding_q:
                submitted_code = request.POST.get('student_code', '')
                language = request.POST.get('programming_language', 'python')

                # Call Gemini AI code evaluation
                eval_result = evaluate_student_code_with_ai(
                    problem_statement=coding_q.problem_statement,
                    student_code=submitted_code,
                    language=language,
                    max_marks=coding_q.marks
                )

                marks_earned = float(eval_result.get('marks_awarded', 0.0))
                total_score = marks_earned

                CodingAnswerSubmission.objects.update_or_create(
                    attempt=attempt,
                    question=coding_q,
                    defaults={
                        'submitted_code': submitted_code,
                        'programming_language': language,
                        'marks_obtained': marks_earned,
                        'ai_correctness_notes': eval_result.get('correctness_feedback', ''),
                        'ai_code_quality_notes': eval_result.get('code_quality_feedback', ''),
                        'ai_edge_case_notes': eval_result.get('edge_case_feedback', ''),
                        'ai_complexity_notes': eval_result.get('complexity_feedback', ''),
                        'ai_suggestions': eval_result.get('suggestions', '')
                    }
                )

                attempt.total_score = total_score
                attempt.ai_feedback_summary = eval_result.get('correctness_feedback', '')
                attempt.is_evaluated = True

        attempt.save()

    messages.success(request, "Your test was submitted and evaluated successfully!")
    return redirect('tests_module:test_result', attempt_id=attempt.id)


@login_required
def test_result(request, attempt_id):
    attempt = get_object_or_404(TestAttempt, id=attempt_id)
    test = attempt.test

    # Security check: only the student who took it, or staff/admin can view
    is_owner = hasattr(request.user, 'student') and request.user.student.id == attempt.student_id
    role = get_user_role(request.user)
    if not (is_owner or role in ['STAFF', 'SUPER_ADMIN']):
        messages.error(request, "You do not have access to view this result.")
        return redirect('/')

    # Calculate rank in batch for this test
    rank = TestAttempt.objects.filter(
        test=test,
        total_score__gt=attempt.total_score
    ).count() + 1
    total_takers = TestAttempt.objects.filter(test=test).count()

    mcq_answers = attempt.mcq_answers.select_related('question').all() if test.test_type == 'MCQ' else None
    coding_answer = attempt.coding_answers.select_related('question').first() if test.test_type == 'CODING' else None

    return render(request, 'tests_module/test_result.html', {
        'attempt': attempt,
        'test': test,
        'rank': rank,
        'total_takers': total_takers,
        'mcq_answers': mcq_answers,
        'coding_answer': coding_answer,
    })
