"""Black Box Testing Tahap 4: fitur pengajuan bantuan warga.
Jalankan: python manage.py test warga
"""
from django.test import TestCase

from accounts.models import User
from pengajuan.models import JenisBantuan, Pengajuan, Warga


class ProfileWargaTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="warga_profile", password="kelurahan123", role=User.Role.WARGA)
        self.warga = Warga.objects.create(user=self.user, nama="Warga Baru", nik="3573010101990002", rt="003", rw="004")
        self.client.login(username="warga_profile", password="kelurahan123")

    def test_profile_page_terbuka_dan_menampilkan_form_password(self):
        response = self.client.get("/warga/profile/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Profil")
        self.assertContains(response, 'name="old_password"')
        self.assertContains(response, 'name="new_password1"')
        self.assertContains(response, 'name="new_password2"')

    def test_warga_bisa_ubah_profil_dan_password(self):
        response = self.client.post("/warga/profile/", {
            "nama": "Warga Updated",
            "rt": "004",
            "rw": "005",
            "email": "warga@email.com",
            "old_password": "kelurahan123",
            "new_password1": "passBaru123",
            "new_password2": "passBaru123",
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.warga.refresh_from_db()
        self.user.refresh_from_db()
        self.assertEqual(self.warga.nama, "Warga Updated")
        self.assertEqual(self.user.email, "warga@email.com")
        self.assertTrue(self.user.check_password("passBaru123"))


class PengajuanBantuanTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="citra", password="kelurahan123", role=User.Role.WARGA)
        self.warga = Warga.objects.create(user=self.user, nama="Citra Dewi", nik="3573010101990002", rt="003", rw="004")
        self.jenis = JenisBantuan.objects.create(nama_bantuan="Bantuan Pangan Non-Tunai (BPNT)", status=True)
        self.jenis_nonaktif = JenisBantuan.objects.create(nama_bantuan="Bantuan Lama (nonaktif)", status=False)
        self.client.login(username="citra", password="kelurahan123")

    def test_ajukan_bantuan_berhasil_dan_status_awal_benar(self):
        response = self.client.post("/warga/ajukan/", {
            "jenis_bantuan": self.jenis.id,
            "pekerjaan": "Wiraswasta",
            "daya_listrik": "900 VA",
            "kondisi_rumah": "Milik Sendiri",
            "jumlah_tanggungan": 3,
            "penghasilan": 1500000,
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        pengajuan = Pengajuan.objects.get(warga=self.warga)
        self.assertEqual(pengajuan.status, Pengajuan.Status.MENUNGGU_VERIFIKASI_DESIL)
        self.assertIsNone(pengajuan.desil)  # desil belum diisi, itu tugas validator
        self.assertEqual(pengajuan.jumlah_tanggungan, 3)
        self.assertEqual(pengajuan.pekerjaan, "Wiraswasta")
        self.assertEqual(pengajuan.daya_listrik, "900 VA")
        self.assertEqual(pengajuan.kondisi_rumah, "Milik Sendiri")

    def test_jenis_bantuan_nonaktif_tidak_bisa_dipilih(self):
        response = self.client.post("/warga/ajukan/", {
            "jenis_bantuan": self.jenis_nonaktif.id,
            "jumlah_tanggungan": 2,
            "penghasilan": 1000000,
        })
        self.assertEqual(response.status_code, 200)  # form invalid, render ulang
        self.assertFalse(Pengajuan.objects.filter(warga=self.warga).exists())

    def test_field_wajib_divalidasi(self):
        response = self.client.post("/warga/ajukan/", {
            "jenis_bantuan": "", "jumlah_tanggungan": "", "penghasilan": "",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Pengajuan.objects.filter(warga=self.warga).exists())

    def test_pengajuan_aktif_jenis_yang_sama_ditolak_agar_tidak_duplikat(self):
        Pengajuan.objects.create(
            warga=self.warga,
            jenis_bantuan=self.jenis,
            pekerjaan="Wiraswasta",
            daya_listrik="900 VA",
            kondisi_rumah="Milik Sendiri",
            jumlah_tanggungan=2,
            penghasilan=900000,
            status=Pengajuan.Status.MENUNGGU_VERIFIKASI_DESIL,
        )

        response = self.client.post("/warga/ajukan/", {
            "jenis_bantuan": self.jenis.id,
            "pekerjaan": "Wiraswasta",
            "daya_listrik": "900 VA",
            "kondisi_rumah": "Milik Sendiri",
            "jumlah_tanggungan": 5,
            "penghasilan": 2000000,
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Pengajuan.objects.filter(warga=self.warga, jenis_bantuan=self.jenis).count(), 1)
        self.assertContains(response, "data yang pernah diajukan")

    def test_pengajuan_final_tidak_boleh_berubah_data_ketika_diajukan_ulang(self):
        Pengajuan.objects.create(
            warga=self.warga,
            jenis_bantuan=self.jenis,
            pekerjaan="Wiraswasta",
            daya_listrik="900 VA",
            kondisi_rumah="Milik Sendiri",
            jumlah_tanggungan=2,
            penghasilan=900000,
            status=Pengajuan.Status.DISETUJUI,
        )

        response = self.client.post("/warga/ajukan/", {
            "jenis_bantuan": self.jenis.id,
            "pekerjaan": "Wiraswasta",
            "daya_listrik": "900 VA",
            "kondisi_rumah": "Milik Sendiri",
            "jumlah_tanggungan": 5,
            "penghasilan": 2000000,
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Pengajuan.objects.filter(warga=self.warga, jenis_bantuan=self.jenis).count(), 1)
        self.assertContains(response, "data yang pernah diajukan")

    def test_riwayat_hanya_tampilkan_pengajuan_sendiri(self):
        Pengajuan.objects.create(warga=self.warga, jenis_bantuan=self.jenis, jumlah_tanggungan=2, penghasilan=900000)

        user_lain = User.objects.create_user(username="dedi", password="kelurahan123", role=User.Role.WARGA)
        warga_lain = Warga.objects.create(user=user_lain, nama="Dedi", nik="3573010101990003", rt="005", rw="006")
        Pengajuan.objects.create(warga=warga_lain, jenis_bantuan=self.jenis, jumlah_tanggungan=1, penghasilan=2000000)

        response = self.client.get("/warga/riwayat/")
        self.assertEqual(len(response.context["daftar_pengajuan"]), 1)
        self.assertEqual(response.context["daftar_pengajuan"][0].warga, self.warga)

    def test_tidak_bisa_buka_detail_pengajuan_warga_lain(self):
        user_lain = User.objects.create_user(username="edo", password="kelurahan123", role=User.Role.WARGA)
        warga_lain = Warga.objects.create(user=user_lain, nama="Edo", nik="3573010101990004", rt="007", rw="008")
        pengajuan_orang_lain = Pengajuan.objects.create(warga=warga_lain, jenis_bantuan=self.jenis, jumlah_tanggungan=1, penghasilan=2000000)

        response = self.client.get(f"/warga/riwayat/{pengajuan_orang_lain.pk}/")
        self.assertEqual(response.status_code, 404)

    def test_riwayat_tidak_mengandung_kata_rekomendasi_atau_prediksi(self):
        """Pastikan halaman status warga tidak pernah membocorkan istilah
        rekomendasi/prediksi ML, sesuai requirement 'warga tidak boleh
        lihat rekomendasi ML'."""
        Pengajuan.objects.create(warga=self.warga, jenis_bantuan=self.jenis, jumlah_tanggungan=2, penghasilan=900000)
        response = self.client.get("/warga/riwayat/")
        content = response.content.decode().lower()
        self.assertNotIn("rekomendasi", content)
        self.assertNotIn("prediksi", content)
        self.assertNotIn("layak", content)
