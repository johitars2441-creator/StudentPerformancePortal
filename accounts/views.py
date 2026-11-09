from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from accounts.decorators import get_user_role


@login_required
def role_redirect(request):
    role = get_user_role(request.user)

    if role == 'SUPER_ADMIN':
        return redirect('/analytics/dashboard/')

    if role == 'STAFF':
        return redirect('/batches/')

    if role == 'STUDENT':
        return redirect('/student/dashboard/')

    # Default fallback
    return redirect('/student/dashboard/')
