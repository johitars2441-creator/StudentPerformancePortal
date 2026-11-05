from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden
from django.db import IntegrityError, transaction

from accounts.models import UserProfile
from .models import Attendance
from .forms import AttendanceForm


@login_required
def manage_attendance(request):
    profile = getattr(request.user, 'userprofile', None)

    # Allow only admins
    if not (
        request.user.is_superuser
        or (profile and profile.role == 'ADMIN')
    ):
        return HttpResponseForbidden(
            'You do not have permission to access this page.'
        )

    message = None

    if request.method == 'POST':
        form = AttendanceForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()

                return redirect('manage_attendance')

            except IntegrityError:
                message = (
                    'Attendance already exists for this student '
                    'on the selected date.'
                )
    else:
        form = AttendanceForm()

    attendance_records = Attendance.objects.select_related(
        'student'
    ).order_by('-date', 'student__roll_number')

    context = {
        'form': form,
        'attendance_records': attendance_records,
        'message': message,
    }

    return render(
        request,
        'attendance/manage_attendance.html',
        context,
    )