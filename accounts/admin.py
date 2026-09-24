from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


class UserAdmin(BaseUserAdmin):
    """UserAdmin bawaan Django tidak otomatis menampilkan field custom
    kita (role), jadi field-nya ditambahkan manual ke fieldsets di sini --
    supaya 'role' bisa diisi langsung dari form tambah/edit user di admin."""

    fieldsets = BaseUserAdmin.fieldsets + (
        ("Role SADEKA", {"fields": ("role",)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Role SADEKA", {"fields": ("role",)}),
    )
    list_display = ("username", "role", "is_staff", "is_active")
    list_filter = BaseUserAdmin.list_filter + ("role",)


admin.site.register(User, UserAdmin)
