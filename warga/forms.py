from django import forms

from pengajuan.models import JenisBantuan, Pengajuan, Warga


class PengajuanForm(forms.ModelForm):
    """Form pengajuan bantuan untuk warga. NIK/RT/RW sengaja TIDAK ada di
    sini -- sudah tersimpan di profil Warga saat registrasi (Tahap 3) dan
    diambil otomatis lewat request.user.warga_profile di view, bukan
    diinput ulang di setiap pengajuan."""

    class Meta:
        model = Pengajuan
        fields = ["jenis_bantuan", "jumlah_tanggungan", "penghasilan"]
        widgets = {
            "jenis_bantuan": forms.Select(attrs={"class": "form-select"}),
            "jumlah_tanggungan": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "penghasilan": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
        }
        labels = {
            "jenis_bantuan": "Jenis bantuan yang diajukan",
            "jumlah_tanggungan": "Jumlah tanggungan keluarga",
            "penghasilan": "Penghasilan per bulan (Rp)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # hanya jenis bantuan yang masih aktif (status=True) yang bisa dipilih
        self.fields["jenis_bantuan"].queryset = JenisBantuan.objects.filter(status=True)


class ProfileForm(forms.ModelForm):
    email = forms.EmailField(required=False, label="Email")

    class Meta:
        model = Warga
        fields = ["nama", "rt", "rw"]
        labels = {
            "nama": "Nama lengkap",
            "rt": "RT",
            "rw": "RW",
        }
        widgets = {
            "nama": forms.TextInput(attrs={"class": "form-control"}),
            "rt": forms.TextInput(attrs={"class": "form-control"}),
            "rw": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user_id:
            self.fields["email"].initial = self.instance.user.email

    def save(self, commit=True):
        warga = super().save(commit=commit)
        warga.user.email = self.cleaned_data["email"]
        if commit:
            warga.user.save(update_fields=["email"])
        return warga
