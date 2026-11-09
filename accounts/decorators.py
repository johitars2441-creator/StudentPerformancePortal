from functools import wraps
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from batches.models import Batch, BatchStaffAssignment


def get_user_role(user):
    if not user.is_authenticated:
        return None
    if user.is_superuser:
        return 'SUPER_ADMIN'
    if hasattr(user, 'userprofile'):
        role = user.userprofile.role
        if role == 'ADMIN':
            return 'SUPER_ADMIN'
        return role
    return None


def super_admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/accounts/login/?next=' + request.path)
        role = get_user_role(request.user)
        if role != 'SUPER_ADMIN':
            messages.error(request, "Access denied. Super Admin privileges required.")
            raise PermissionDenied("Super Admin access required.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def staff_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/accounts/login/?next=' + request.path)
        role = get_user_role(request.user)
        if role not in ['STAFF', 'SUPER_ADMIN']:
            messages.error(request, "Access denied. Staff privileges required.")
            raise PermissionDenied("Staff access required.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def student_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/accounts/login/?next=' + request.path)
        role = get_user_role(request.user)
        if role != 'STUDENT' and not request.user.is_superuser:
            messages.error(request, "Access denied. Student privileges required.")
            raise PermissionDenied("Student access required.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def can_access_batch(user, batch):
    """
    Returns True if user is Super Admin or Staff assigned to the batch.
    """
    if not user.is_authenticated:
        return False
    role = get_user_role(user)
    if role == 'SUPER_ADMIN':
        return True
    if role == 'STAFF':
        return BatchStaffAssignment.objects.filter(batch=batch, staff=user).exists()
    if role == 'STUDENT':
        return hasattr(user, 'student') and user.student.batch_id == batch.id
    return False

