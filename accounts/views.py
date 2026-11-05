
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


@login_required
def role_redirect(request):
    user = request.user

    if user.is_superuser or user.is_staff:
        return redirect('/analytics/dashboard/')

    if hasattr(user, 'userprofile'):
        if user.userprofile.role == 'ADMIN':
            return redirect('/analytics/dashboard/')

    return redirect('/student/dashboard/')
