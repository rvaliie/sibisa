"""
Black Box Testing Tahap 3: alur registrasi warga, login, dan pembatasan
akses berbasis role. Jalankan dengan: python manage.py test accounts
"""
from django.test import TestCase

from accounts.models import User
from pengajuan.models import Warga


class RegistrasiWargaTest(TestCase):
    def test_registrasi_warga_membuat_user_dan_profil(self):
        response = self.client.post("/accounts/register/", {
            "username": "budi",
            "nama": "Budi Santoso",
            "nik": "3573010101990001",
            "rt": "001",
            "rw": "002",
            "password1": "kelurahan123",
            "password2": "kelurahan123",
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username="budi", role=User.Role.WARGA).exists())
        self.assertTrue(Warga.objects.filter(nik="3573010101990001").exists())
        # setelah registrasi, langsung login dan diarahkan ke dashboard warga
        self.assertRedirects(response, "/warga/dashboard/")

    def test_nik_duplikat_ditolak(self):
        User.objects.create_user(username="budi1", password="x", role=User.Role.WARGA)
        Warga.objects.create(user=User.objects.get(username="budi1"), nama="A", nik="1111111111111111", rt="1", rw="1")
        response = self.client.post("/accounts/register/", {
            "username": "budi2", "nama": "B", "nik": "1111111111111111",
            "rt": "2", "rw": "2", "password1": "kelurahan123", "password2": "kelurahan123",
        })
        self.assertEqual(response.status_code, 200)  # form invalid, render ulang halaman
        self.assertFalse(User.objects.filter(username="budi2").exists())


class LoginRedirectTest(TestCase):
    def setUp(self):
        self.warga_user = User.objects.create_user(username="warga1", password="kelurahan123", role=User.Role.WARGA)
        Warga.objects.create(user=self.warga_user, nama="Warga Satu", nik="2222222222222222", rt="1", rw="1")
        self.validator_user = User.objects.create_user(username="validator1", password="kelurahan123", role=User.Role.VALIDATOR)

    def test_login_warga_redirect_ke_dashboard_warga(self):
        response = self.client.post("/accounts/login/", {"username": "warga1", "password": "kelurahan123"}, follow=True)
        self.assertRedirects(response, "/warga/dashboard/")

    def test_login_validator_redirect_ke_dashboard_validator(self):
        response = self.client.post("/accounts/login/", {"username": "validator1", "password": "kelurahan123"}, follow=True)
        self.assertRedirects(response, "/validator/dashboard/")

    def test_validator_tidak_bisa_akses_dashboard_warga(self):
        self.client.login(username="validator1", password="kelurahan123")
        response = self.client.get("/warga/dashboard/", follow=True)
        self.assertRedirects(response, "/validator/dashboard/")

    def test_warga_tidak_bisa_akses_dashboard_validator(self):
        self.client.login(username="warga1", password="kelurahan123")
        response = self.client.get("/validator/dashboard/", follow=True)
        self.assertRedirects(response, "/warga/dashboard/")

    def test_anonymous_diarahkan_ke_login(self):
        response = self.client.get("/warga/dashboard/")
        self.assertRedirects(response, "/accounts/login/?next=/warga/dashboard/")


class SuperuserTanpaRoleTest(TestCase):
    """Regresi untuk bug: superuser (role kosong) yang login lalu buka
    /accounts/redirect-after-login/ dulu sempat ERR_TOO_MANY_REDIRECTS
    karena terus dilempar ke warga:dashboard yang menolaknya."""

    def setUp(self):
        User.objects.create_superuser(username="admin", email="", password="admin12345")

    def test_superuser_diarahkan_ke_admin_bukan_loop(self):
        self.client.login(username="admin", password="admin12345")
        response = self.client.get("/accounts/redirect-after-login/", follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, "/admin/")

    def test_superuser_buka_halaman_register_tidak_loop(self):
        self.client.login(username="admin", password="admin12345")
        response = self.client.get("/accounts/register/", follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, "/admin/")


class AdminRoleFieldTest(TestCase):
    """Regresi: pastikan field 'role' benar-benar muncul di form admin
    (bukan cuma bisa diisi lewat shell/API), karena ini jalur utama
    admin kelurahan membuat akun validator."""

    def setUp(self):
        self.admin = User.objects.create_superuser(username="admin", email="", password="admin12345")
        self.client.login(username="admin", password="admin12345")

    def test_field_role_muncul_di_form_tambah_user(self):
        response = self.client.get("/admin/accounts/user/add/")
        self.assertContains(response, 'name="role"')

    def test_field_role_muncul_di_form_edit_user(self):
        target = User.objects.create_user(username="calon_validator", password="x", role=User.Role.WARGA)
        response = self.client.get(f"/admin/accounts/user/{target.pk}/change/")
        self.assertContains(response, 'name="role"')
