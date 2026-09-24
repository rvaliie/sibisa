from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import ValidatorCreateForm, WargaRegisterForm
from .models import User


def register_warga(request):
    """Registrasi mandiri untuk WARGA saja. Validator tidak bisa daftar
    lewat halaman publik ini -- akunnya dibuat manual lewat Django admin."""
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("accounts:redirect_after_login")

    if request.method == "POST":
        form = WargaRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("accounts:redirect_after_login")
    else:
        form = WargaRegisterForm()

    return render(request, "accounts/register.html", {"form": form})


@login_required
def redirect_after_login(request):
    """Satu pintu redirect setelah login: warga -> dashboard warga,
    validator -> dashboard validator. Akun tanpa role (mis. superuser yang
    dibuat lewat createsuperuser) TIDAK diarahkan ke salah satu dashboard --
    itu penyebab redirect loop sebelumnya -- melainkan ke /admin/ (kalau
    staff) atau logout."""
    if request.user.role == User.Role.VALIDATOR:
        return redirect("validator:dashboard")
    if request.user.role == User.Role.WARGA:
        return redirect("warga:dashboard")

    if request.user.is_staff:
        messages.info(request, "Akun ini adalah akun admin/superuser, bukan Warga atau Validator.")
        return redirect("/admin/")

    messages.error(request, "Akun ini belum memiliki role Warga/Validator yang valid.")
    return redirect("accounts:logout")


@login_required
def buat_validator(request):
    """Halaman buat akun Validator. Hanya bisa diakses oleh superuser/staff
    (admin kelurahan). Validator tidak bisa daftar sendiri lewat halaman publik."""
    if not request.user.is_superuser:
        messages.error(request, "Halaman ini hanya bisa diakses oleh admin kelurahan.")
        return redirect("accounts:redirect_after_login")

    # Ambil semua validator yang sudah ada untuk ditampilkan
    daftar_validator = User.objects.filter(role=User.Role.VALIDATOR).order_by("username")

    if request.method == "POST":
        form = ValidatorCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Akun validator '{user.username}' berhasil dibuat.")
            return redirect("accounts:buat_validator")
    else:
        form = ValidatorCreateForm()

    return render(request, "accounts/buat_validator.html", {
        "form": form,
        "daftar_validator": daftar_validator,
    })

