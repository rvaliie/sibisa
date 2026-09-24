"""Black Box Testing Tahap 5: dashboard validator, detail pengajuan
(NIK penuh vs masked), dan input desil manual.
Jalankan: python manage.py test validator
"""
from django.test import TestCase

from accounts.models import User
from pengajuan.models import JenisBantuan, Pengajuan, Warga
from pengajuan.utils import mask_nik


class MaskNikTest(TestCase):
    def test_mask_nik_format(self):
        self.assertEqual(mask_nik("3573010101990002"), "357301******0002")

    def test_mask_nik_pendek_tidak_error(self):
        self.assertEqual(mask_nik("123"), "***")


class DashboardValidatorTest(TestCase):
    def setUp(self):
        self.validator = User.objects.create_user(username="validator1", password="kelurahan123", role=User.Role.VALIDATOR)
        warga_user = User.objects.create_user(username="fitri", password="x", role=User.Role.WARGA)
        self.warga = Warga.objects.create(user=warga_user, nama="Fitri", nik="3573010101990005", rt="001", rw="001")
        self.jenis = JenisBantuan.objects.create(nama_bantuan="BPNT", status=True)
        self.pengajuan = Pengajuan.objects.create(warga=self.warga, jenis_bantuan=self.jenis, jumlah_tanggungan=2, penghasilan=1000000)
        self.client.login(username="validator1", password="kelurahan123")

    def test_dashboard_menampilkan_nik_yang_dimask_bukan_asli(self):
        response = self.client.get("/validator/dashboard/")
        content = response.content.decode()
        self.assertNotIn("3573010101990005", content)  # NIK asli tidak boleh muncul di daftar
        self.assertIn("357301", content)  # tapi versi mask-nya muncul

    def test_detail_menampilkan_nik_penuh(self):
        response = self.client.get(f"/validator/pengajuan/{self.pengajuan.pk}/")
        self.assertContains(response, "3573010101990005")  # detail butuh NIK penuh untuk cek manual

    def test_input_desil_berhasil_tersimpan(self):
        response = self.client.post(f"/validator/pengajuan/{self.pengajuan.pk}/", {"desil": 3, "submit_desil": "1"}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.pengajuan.refresh_from_db()
        self.assertEqual(self.pengajuan.desil, 3)

    def test_desil_di_luar_rentang_ditolak(self):
        response = self.client.post(f"/validator/pengajuan/{self.pengajuan.pk}/", {"desil": 15, "submit_desil": "1"})
        self.assertEqual(response.status_code, 200)
        self.pengajuan.refresh_from_db()
        self.assertIsNone(self.pengajuan.desil)

    def test_warga_tidak_bisa_akses_dashboard_validator(self):
        self.client.logout()
        user_warga = User.objects.create_user(username="warga_x", password="kelurahan123", role=User.Role.WARGA)
        Warga.objects.create(user=user_warga, nama="Warga X", nik="9999999999999999", rt="1", rw="1")
        self.client.login(username="warga_x", password="kelurahan123")
        response = self.client.get("/validator/dashboard/", follow=True)
        self.assertNotEqual(response.request["PATH_INFO"], "/validator/dashboard/")


class PrediksiMLIntegrationTest(TestCase):
    """Tahap 8: tombol Jalankan Prediksi di halaman detail validator.
    Butuh model.joblib sudah dilatih (lihat pengajuan/tests.py TrainingTest
    yang melatihnya lewat train_main(), jadi test ini dijalankan setelah
    itu -- untuk aman, dilatih ulang eksplisit di setUpClass)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from ml_engine.train import main as train_main
        train_main()

    def setUp(self):
        self.validator = User.objects.create_user(username="validator2", password="kelurahan123", role=User.Role.VALIDATOR)
        warga_user = User.objects.create_user(username="gilang", password="x", role=User.Role.WARGA)
        self.warga = Warga.objects.create(user=warga_user, nama="Gilang", nik="3573010101990006", rt="002", rw="002")
        self.jenis = JenisBantuan.objects.create(nama_bantuan="BPNT", status=True)
        self.pengajuan = Pengajuan.objects.create(warga=self.warga, jenis_bantuan=self.jenis, jumlah_tanggungan=4, penghasilan=500000)
        self.client.login(username="validator2", password="kelurahan123")

    def test_prediksi_ditolak_kalau_desil_belum_diisi(self):
        response = self.client.post(f"/validator/pengajuan/{self.pengajuan.pk}/", {"jalankan_prediksi": "1"}, follow=True)
        self.pengajuan.refresh_from_db()
        self.assertEqual(self.pengajuan.status, Pengajuan.Status.MENUNGGU_VERIFIKASI_DESIL)
        self.assertFalse(hasattr(self.pengajuan, "hasil_prediksi"))

    def test_prediksi_berhasil_setelah_desil_diisi(self):
        self.pengajuan.desil = 2
        self.pengajuan.save()

        response = self.client.post(f"/validator/pengajuan/{self.pengajuan.pk}/", {"jalankan_prediksi": "1"}, follow=True)
        self.assertEqual(response.status_code, 200)

        self.pengajuan.refresh_from_db()
        self.assertEqual(self.pengajuan.status, Pengajuan.Status.REKOMENDASI_TERSEDIA)
        self.assertTrue(hasattr(self.pengajuan, "hasil_prediksi"))
        hasil = self.pengajuan.hasil_prediksi
        self.assertIn(hasil.prediksi, ["LAYAK", "TIDAK_LAYAK"])
        self.assertGreaterEqual(hasil.probabilitas, 0.0)
        self.assertLessEqual(hasil.probabilitas, 1.0)

    def test_jalankan_ulang_prediksi_update_bukan_duplikat(self):
        from pengajuan.models import HasilPrediksi
        self.pengajuan.desil = 2
        self.pengajuan.save()

        self.client.post(f"/validator/pengajuan/{self.pengajuan.pk}/", {"jalankan_prediksi": "1"})
        self.client.post(f"/validator/pengajuan/{self.pengajuan.pk}/", {"jalankan_prediksi": "1"})

        self.assertEqual(HasilPrediksi.objects.filter(pengajuan=self.pengajuan).count(), 1)

    def test_rekomendasi_muncul_di_halaman_detail_validator(self):
        self.pengajuan.desil = 2
        self.pengajuan.save()
        self.client.post(f"/validator/pengajuan/{self.pengajuan.pk}/", {"jalankan_prediksi": "1"})

        response = self.client.get(f"/validator/pengajuan/{self.pengajuan.pk}/")
        content = response.content.decode()
        self.assertIn("Rekomendasi Sistem", content)
        self.assertIn("rekomendasi awal", content.lower())


class KeputusanAkhirTest(TestCase):
    """Tahap 9: FR-11 & FR-12 -- validator menetapkan keputusan akhir
    (disetujui/ditolak) beserta catatan, setelah rekomendasi tersedia."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from ml_engine.train import main as train_main
        train_main()

    def setUp(self):
        self.validator = User.objects.create_user(username="validator3", password="kelurahan123", role=User.Role.VALIDATOR)
        warga_user = User.objects.create_user(username="hana", password="x", role=User.Role.WARGA)
        self.warga = Warga.objects.create(user=warga_user, nama="Hana", nik="3573010101990007", rt="003", rw="003")
        self.jenis = JenisBantuan.objects.create(nama_bantuan="BPNT", status=True)
        self.pengajuan = Pengajuan.objects.create(warga=self.warga, jenis_bantuan=self.jenis, jumlah_tanggungan=3, penghasilan=800000)
        self.client.login(username="validator3", password="kelurahan123")

    def test_keputusan_ditolak_sebelum_rekomendasi_tersedia(self):
        response = self.client.post(f"/validator/pengajuan/{self.pengajuan.pk}/",
                                     {"submit_keputusan": "1", "keputusan": "DISETUJUI", "catatan": "uji"}, follow=True)
        self.pengajuan.refresh_from_db()
        self.assertEqual(self.pengajuan.status, Pengajuan.Status.MENUNGGU_VERIFIKASI_DESIL)
        self.assertFalse(hasattr(self.pengajuan, "verifikasi"))

    def test_keputusan_berhasil_setelah_rekomendasi_tersedia(self):
        from pengajuan.models import Verifikasi
        self.pengajuan.desil = 2
        self.pengajuan.save()
        self.client.post(f"/validator/pengajuan/{self.pengajuan.pk}/", {"jalankan_prediksi": "1"})

        response = self.client.post(f"/validator/pengajuan/{self.pengajuan.pk}/",
                                     {"submit_keputusan": "1", "keputusan": "DISETUJUI", "catatan": "Sesuai kriteria"},
                                     follow=True)
        self.assertEqual(response.status_code, 200)

        self.pengajuan.refresh_from_db()
        self.assertEqual(self.pengajuan.status, Pengajuan.Status.DISETUJUI)
        verif = self.pengajuan.verifikasi
        self.assertEqual(verif.keputusan, Verifikasi.Keputusan.DISETUJUI)
        self.assertEqual(verif.catatan, "Sesuai kriteria")
        self.assertEqual(verif.validator, self.validator)

    def test_keputusan_ditolak_mengubah_status_ditolak(self):
        self.pengajuan.desil = 8
        self.pengajuan.save()
        self.client.post(f"/validator/pengajuan/{self.pengajuan.pk}/", {"jalankan_prediksi": "1"})
        self.client.post(f"/validator/pengajuan/{self.pengajuan.pk}/",
                          {"submit_keputusan": "1", "keputusan": "DITOLAK", "catatan": ""})
        self.pengajuan.refresh_from_db()
        self.assertEqual(self.pengajuan.status, Pengajuan.Status.DITOLAK)

    def test_keputusan_bisa_diperbarui_bukan_duplikat(self):
        from pengajuan.models import Verifikasi
        self.pengajuan.desil = 2
        self.pengajuan.save()
        self.client.post(f"/validator/pengajuan/{self.pengajuan.pk}/", {"jalankan_prediksi": "1"})
        self.client.post(f"/validator/pengajuan/{self.pengajuan.pk}/",
                          {"submit_keputusan": "1", "keputusan": "DITOLAK", "catatan": "awal"})
        self.client.post(f"/validator/pengajuan/{self.pengajuan.pk}/",
                          {"submit_keputusan": "1", "keputusan": "DISETUJUI", "catatan": "revisi"})

        self.assertEqual(Verifikasi.objects.filter(pengajuan=self.pengajuan).count(), 1)
        self.pengajuan.refresh_from_db()
        self.assertEqual(self.pengajuan.status, Pengajuan.Status.DISETUJUI)
        self.assertEqual(self.pengajuan.verifikasi.catatan, "revisi")

    def test_warga_hanya_lihat_status_bukan_keputusan_detail(self):
        """Regresi: pastikan status Disetujui/Ditolak yang dilihat warga
        tidak disertai catatan verifikasi atau info rekomendasi ML."""
        self.pengajuan.desil = 2
        self.pengajuan.save()
        self.client.post(f"/validator/pengajuan/{self.pengajuan.pk}/", {"jalankan_prediksi": "1"})
        self.client.post(f"/validator/pengajuan/{self.pengajuan.pk}/",
                          {"submit_keputusan": "1", "keputusan": "DISETUJUI", "catatan": "rahasia validator"})

        self.client.logout()
        self.client.login(username=self.warga.user.username, password="x")
        response = self.client.get(f"/warga/riwayat/{self.pengajuan.pk}/")
        content = response.content.decode()
        self.assertIn("Disetujui", content)
        self.assertNotIn("rahasia validator", content)
        self.assertNotIn("Layak", content)
        self.assertNotIn("probabilitas", content.lower())
