from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user, hanya menambahkan field role di atas AbstractUser bawaan Django.
    Kenapa custom User dari awal: Django tidak mengizinkan ganti AUTH_USER_MODEL
    setelah migrasi pertama dijalankan, jadi ini wajib disiapkan sejak Tahap 2.
    """

    class Role(models.TextChoices):
        WARGA = "WARGA", "Warga"
        VALIDATOR = "VALIDATOR", "Validator Kelurahan"

    role = models.CharField(max_length=20, choices=Role.choices)

    def is_warga(self):
        return self.role == self.Role.WARGA

    def is_validator(self):
        return self.role == self.Role.VALIDATOR
