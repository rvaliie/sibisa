from django.urls import path

from . import views

app_name = "validator"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("data-pengajuan/", views.data_pengajuan, name="data_pengajuan"),
    path("riwayat/", views.riwayat_pengajuan, name="riwayat_pengajuan"),
    path("pengajuan/<int:pk>/", views.detail_pengajuan, name="detail_pengajuan"),
]
