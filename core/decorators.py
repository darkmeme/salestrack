from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required


def superadmin_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_superadmin:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper


def branch_admin_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.is_cashier:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper
