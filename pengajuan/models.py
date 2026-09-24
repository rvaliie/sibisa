from django.conf import settings
from django.db import models


class Warga(models.Model):
    """Profil tambahan untuk User berrole WARGA. NIK disimpan apa adanya di
    database (bukan tampilan), tapi WAJIB dimask saat ditampilkan di
    dashboard/dokumentasi -- lihat pengajuan/utils.py yang dibuat di Tahap 4."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="warga_profile")
    nama = models.CharField(max_length=150)
    nik = models.CharField(max_length=16, unique=True)
    rt = models.CharField(max_length=5)
    rw = models.CharField(max_length=5)

    def __str__(self):
        return f"{self.nama} ({self.nik})"


class JenisBantuan(models.Model):
    nama_bantuan = models.CharField(max_length=150)
    deskripsi = models.TextField(blank=True)
    status = models.BooleanField(default=True)  # aktif/tidak aktif

    def __str__(self):
        return self.nama_bantuan


class Pengajuan(models.Model):
    class Status(models.TextChoices):
        MENUNGGU_VERIFIKASI_DESIL = "MENUNGGU_VERIFIKASI_DESIL", "Menunggu Verifikasi Desil"
        REKOMENDASI_TERSEDIA = "REKOMENDASI_TERSEDIA", "Rekomendasi Tersedia"
        DISETUJUI = "DISETUJUI", "Disetujui"
        DITOLAK = "DITOLAK", "Ditolak"

    warga = models.ForeignKey(Warga, on_delete=models.CASCADE, related_name="pengajuan_list")
    jenis_bantuan = models.ForeignKey(JenisBantuan, on_delete=models.PROTECT, related_name="pengajuan_list")
    jumlah_tanggungan = models.PositiveSmallIntegerField()
    penghasilan = models.PositiveIntegerField(help_text="Rupiah per bulan")
    # desil sengaja nullable: diisi belakangan oleh validator, bukan oleh warga
    desil = models.PositiveSmallIntegerField(null=True, blank=True)
    tanggal_pengajuan = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.MENUNGGU_VERIFIKASI_DESIL)

    def __str__(self):
        return f"Pengajuan #{self.pk} - {self.warga.nama}"


class HasilPrediksi(models.Model):
    class Prediksi(models.TextChoices):
        LAYAK = "LAYAK", "Layak"
        TIDAK_LAYAK = "TIDAK_LAYAK", "Tidak Layak"

    pengajuan = models.OneToOneField(Pengajuan, on_delete=models.CASCADE, related_name="hasil_prediksi")
    prediksi = models.CharField(max_length=20, choices=Prediksi.choices)
    probabilitas = models.FloatField(help_text="Probabilitas kelas prediksi, 0-1")
    model_digunakan = models.CharField(max_length=50, help_text="mis. decision_tree_v1")
    tanggal_prediksi = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Prediksi {self.pengajuan_id}: {self.prediksi} ({self.probabilitas:.0%})"


class Verifikasi(models.Model):
    class Keputusan(models.TextChoices):
        DISETUJUI = "DISETUJUI", "Disetujui"
        DITOLAK = "DITOLAK", "Ditolak"

    pengajuan = models.OneToOneField(Pengajuan, on_delete=models.CASCADE, related_name="verifikasi")
    validator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="verifikasi_list")
    keputusan = models.CharField(max_length=20, choices=Keputusan.choices)
    catatan = models.TextField(blank=True)
    tanggal_verifikasi = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Verifikasi {self.pengajuan_id}: {self.keputusan}"


class DataHistoris(models.Model):
    """Dataset terpisah untuk training ML, TIDAK terhubung FK ke Pengajuan.
    Diisi lewat import CSV (lihat data/data_historis_dummy.csv), bukan lewat alur transaksi."""

    class Status(models.TextChoices):
        DITERIMA = "DITERIMA", "Diterima"
        DITOLAK = "DITOLAK", "Ditolak"

    desil = models.PositiveSmallIntegerField()
    jumlah_tanggungan = models.PositiveSmallIntegerField()
    penghasilan = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=Status.choices)

    def __str__(self):
        return f"Historis desil={self.desil}, status={self.status}"
