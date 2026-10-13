from django import forms

from accounts.models import User
from pengajuan.models import Pengajuan, Verifikasi


class ValidatorProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name"]
        labels = {"first_name": "Nama Lengkap"}
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Masukkan nama lengkap"}),
        }


class DesilForm(forms.ModelForm):
    """FR-08: validator memasukkan hasil desil yang diperoleh dari
    pengecekan manual NIK di web pusat. Bukan otomatis -- validator yang
    mengetik angkanya sendiri setelah melihat hasil di web pusat."""

    class Meta:
        model = Pengajuan
        fields = ["desil"]
        widgets = {
            "desil": forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 10}),
        }
        labels = {"desil": "Desil (hasil cek manual di web pusat)"}

    def clean_desil(self):
        desil = self.cleaned_data["desil"]
        if desil is None or not (1 <= desil <= 10):
            raise forms.ValidationError("Desil harus antara 1 sampai 10.")
        return desil


class KeputusanForm(forms.ModelForm):
    """FR-11 & FR-12: validator menetapkan keputusan akhir (disetujui/
    ditolak) beserta catatan verifikasi. Rekomendasi sistem (hasil_prediksi)
    hanya jadi bahan pertimbangan -- keputusan akhir tetap pilihan manual
    validator, bukan otomatis mengikuti hasil ML."""

    class Meta:
        model = Verifikasi
        fields = ["keputusan", "catatan"]
        widgets = {
            "keputusan": forms.Select(attrs={"class": "form-select"}),
            "catatan": forms.Textarea(attrs={"class": "form-control", "rows": 3,
                                              "placeholder": "Catatan verifikasi (opsional)"}),
        }
        labels = {"keputusan": "Keputusan Akhir", "catatan": "Catatan Verifikasi"}

