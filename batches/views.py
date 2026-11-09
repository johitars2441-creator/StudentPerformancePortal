from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db import transaction

from batches.models import Batch, BatchStaffAssignment
from batches.forms import BatchForm, StaffCreationForm, StudentEnrollmentForm
from accounts.models import UserProfile, StaffProfile
from accounts.decorators import (
    super_admin_required,
    staff_required,
    get_user_role,
    can_access_batch
)
from students.models import Student
from subjects.models import Subject


@login_required
@staff_required
def batch_list(request):
    role = get_user_role(request.user)
    if role == 'SUPER_ADMIN':
        batches = Batch.objects.all().prefetch_related('students', 'staff_assignments')
    else:
        # Staff sees only assigned batches
        assigned_batch_ids = BatchStaffAssignment.objects.filter(staff=request.user).values_list('batch_id', flat=True)
        batches = Batch.objects.filter(id__in=assigned_batch_ids).prefetch_related('students', 'staff_assignments')

    return render(request, 'batches/batch_list.html', {
        'batches': batches,
        'is_admin': role == 'SUPER_ADMIN',
    })


@login_required
@super_admin_required
def batch_create(request):
    if request.method == 'POST':
        form = BatchForm(request.POST)
        if form.is_valid():
            batch = form.save()
            messages.success(request, f"Batch '{batch.batch_code} - {batch.batch_name}' created successfully.")
            return redirect('batches:batch_detail', batch_id=batch.id)
    else:
        form = BatchForm()

    return render(request, 'batches/batch_form.html', {
        'form': form,
        'title': 'Create New Unique Batch',
    })


@login_required
@staff_required
def batch_detail(request, batch_id):
    batch = get_object_or_404(Batch, id=batch_id)
    if not can_access_batch(request.user, batch):
        messages.error(request, "You do not have permission to access this batch.")
        return redirect('batches:batch_list')

    students = batch.students.all()
    staff_assignments = batch.staff_assignments.select_related('staff')
    subjects = batch.subjects.all()

    return render(request, 'batches/batch_detail.html', {
        'batch': batch,
        'students': students,
        'staff_assignments': staff_assignments,
        'subjects': subjects,
        'is_admin': get_user_role(request.user) == 'SUPER_ADMIN',
    })


@login_required
@super_admin_required
def batch_assign_staff(request, batch_id):
    batch = get_object_or_404(Batch, id=batch_id)
    staff_users = User.objects.filter(userprofile__role='STAFF')

    if request.method == 'POST':
        selected_staff_ids = request.POST.getlist('staff_ids')
        # Sync staff assignments
        with transaction.atomic():
            BatchStaffAssignment.objects.filter(batch=batch).delete()
            for s_id in selected_staff_ids:
                staff_user = User.objects.filter(id=s_id).first()
                if staff_user:
                    BatchStaffAssignment.objects.create(
                        batch=batch,
                        staff=staff_user,
                        assigned_by=request.user
                    )
        messages.success(request, f"Staff assignments updated for batch {batch.batch_code}.")
        return redirect('batches:batch_detail', batch_id=batch.id)

    currently_assigned_ids = set(batch.staff_assignments.values_list('staff_id', flat=True))

    return render(request, 'batches/batch_assign_staff.html', {
        'batch': batch,
        'staff_users': staff_users,
        'currently_assigned_ids': currently_assigned_ids,
    })


@login_required
@super_admin_required
def manage_staff(request):
    staff_members = StaffProfile.objects.select_related('user_profile__user').all()
    # Also find any User with role='STAFF' who might not have a StaffProfile yet
    users_with_staff_role = User.objects.filter(userprofile__role='STAFF')

    return render(request, 'batches/staff_list.html', {
        'staff_members': staff_members,
        'staff_users': users_with_staff_role,
    })


@login_required
@super_admin_required
def create_staff(request):
    if request.method == 'POST':
        form = StaffCreationForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            with transaction.atomic():
                user = User.objects.create_user(
                    username=data['username'],
                    password=data['password'],
                    email=data['email'],
                    first_name=data.get('first_name', ''),
                    last_name=data.get('last_name', '')
                )
                profile, _ = UserProfile.objects.get_or_create(user=user, defaults={'role': 'STAFF'})
                profile.role = 'STAFF'
                profile.save()

                StaffProfile.objects.create(
                    user_profile=profile,
                    staff_id=data.get('staff_id', '') or f"EMP-{user.id:04d}",
                    department=data.get('department', ''),
                    designation=data.get('designation', '')
                )

            messages.success(request, f"Staff account '{user.username}' created successfully!")
            return redirect('batches:manage_staff')
    else:
        form = StaffCreationForm()

    return render(request, 'batches/staff_form.html', {
        'form': form,
        'title': 'Add New Staff Member',
    })


@login_required
@staff_required
def enroll_student(request, batch_id):
    batch = get_object_or_404(Batch, id=batch_id)
    if not can_access_batch(request.user, batch):
        messages.error(request, "Permission denied for this batch.")
        return redirect('batches:batch_list')

    if request.method == 'POST':
        form = StudentEnrollmentForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            with transaction.atomic():
                user = User.objects.create_user(
                    username=data['username'],
                    password=data['password'],
                    email=data['email'],
                    first_name=data['full_name']
                )
                profile, _ = UserProfile.objects.get_or_create(user=user, defaults={'role': 'STUDENT'})
                profile.role = 'STUDENT'
                profile.save()

                Student.objects.create(
                    user=user,
                    batch=batch,
                    roll_number=data['roll_number'],
                    full_name=data['full_name'],
                    email=data['email'],
                    department=data.get('department', ''),
                    admission_date=data['admission_date'],
                    added_by=request.user
                )

            messages.success(request, f"Student '{data['full_name']}' enrolled in {batch.batch_code} successfully!")
            return redirect('batches:batch_detail', batch_id=batch.id)
    else:
        form = StudentEnrollmentForm()

    return render(request, 'batches/enroll_student.html', {
        'form': form,
        'batch': batch,
    })
