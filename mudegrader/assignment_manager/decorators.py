from django.core.exceptions import PermissionDenied
from authentication.models import Role


def is_teacher(user):
    return user.is_authenticated and user.role == Role.TEACHER


def is_admin(user):
    return user.is_authenticated and user.is_superuser


def teacher_required(view_func):
    def _wrapped_view_func(request, *args, **kwargs):
        if not is_teacher(request.user) and not is_admin(request.user):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return _wrapped_view_func
