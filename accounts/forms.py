from django import forms
from django.contrib.auth.forms import UserCreationForm

from pengajuan.models import Warga
from .models import User


class WargaRegisterForm(UserCreationForm):
    """Form registrasi untuk WARGA. Membuat User (role=WARGA) sekaligus
    profil Warga (nama, NIK, RT, RW) dalam satu submit."""

    nama = forms.CharField(max_length=150, label="Nama lengkap")
    nik = forms.CharField(max_length=16, min_length=16, label="NIK (16 digit)")
    rt = forms.CharField(max_length=5, label="RT")
    rw = forms.CharField(max_length=5, label="RW")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["username", "nama", "nik", "rt", "rw", "password1", "password2"]

    def clean_nik(self):
        nik = self.cleaned_data["nik"]
        if not nik.isdigit():
            raise forms.ValidationError("NIK harus berupa angka.")
        if Warga.objects.filter(nik=nik).exists():
            raise forms.ValidationError("NIK ini sudah terdaftar.")
        return nik

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.WARGA
        if commit:
            user.save()
            Warga.objects.create(
                user=user,
                nama=self.cleaned_data["nama"],
                nik=self.cleaned_data["nik"],
                rt=self.cleaned_data["rt"],
                rw=self.cleaned_data["rw"],
            )
        return user


class ValidatorCreateForm(UserCreationForm):
    """Form untuk membuat akun Validator baru. Hanya bisa diakses oleh
    superuser/admin kelurahan lewat halaman /accounts/buat-validator/.
    Validator tidak bisa mendaftar sendiri."""

    nama_lengkap = forms.CharField(
        max_length=150,
        label="Nama Lengkap Validator",
        help_text="Nama resmi petugas validator kelurahan.",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["username", "nama_lengkap", "password1", "password2"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.VALIDATOR
        # Simpan nama ke first_name supaya mudah diidentifikasi di admin
        user.first_name = self.cleaned_data["nama_lengkap"]
        if commit:
            user.save()
        return user
