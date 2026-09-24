from django.urls import path

from . import views

app_name = "warga"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("ajukan/", views.ajukan_bantuan, name="ajukan_bantuan"),
    path("riwayat/", views.riwayat_pengajuan, name="riwayat"),
    path("riwayat/<int:pk>/", views.detail_pengajuan, name="detail_pengajuan"),
    path("profile/", views.profile, name="profile"),
    path("notifikasi/", views.notifications, name="notifications"),
]
