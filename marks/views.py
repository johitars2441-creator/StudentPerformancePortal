from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden

from accounts.models import UserProfile
from students.models import Student
from subjects.models import Subject
from .models import Marks
from .forms import MarksForm


@login_required
def manage_marks(request):
    profile = getattr(request.user, 'userprofile', None)

    if not (
        request.user.is_superuser
        or (profile and profile.role == 'ADMIN')
    ):
        return HttpResponseForbidden(
            'You do not have permission to access this page.'
        )

    if request.method == 'POST':
        form = MarksForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('manage_marks')
    else:
        form = MarksForm()

    marks_records = Marks.objects.select_related(
        'student', 'subject'
    ).order_by('-exam_date', 'student__roll_number')

    context = {
        'form': form,
        'marks_records': marks_records,
    }

    return render(
        request,
        'marks/manage_marks.html',
        context,
    )