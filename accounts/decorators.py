from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def role_required(role):
    """Membatasi akses view hanya untuk user dengan role tertentu
    (User.Role.WARGA atau User.Role.VALIDATOR). Dipakai di warga/views.py
    dan validator/views.py supaya warga tidak bisa buka halaman validator,
    dan sebaliknya."""

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped(request, *args, **kwargs):
            if request.user.role != role:
                messages.error(request, "Kamu tidak punya akses ke halaman ini.")
                return redirect("accounts:redirect_after_login")
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator
