from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden

from accounts.models import UserProfile
from .models import Subject
from .forms import SubjectForm


@login_required
def manage_subjects(request):
    profile = getattr(request.user, 'userprofile', None)

    # Check admin permission
    if not (
        request.user.is_superuser
        or (profile and profile.role == 'ADMIN')
    ):
        return HttpResponseForbidden(
            'You do not have permission to access this page.'
        )

    # Process submitted form
    if request.method == 'POST':
        form = SubjectForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('manage_subjects')
    else:
        form = SubjectForm()

    subjects = Subject.objects.all().order_by('subject_code')

    context = {
        'form': form,
        'subjects': subjects,
    }

    return render(
        request,
        'subjects/manage_subjects.html',
        context,
    )