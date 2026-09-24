from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import role_required
from accounts.models import User
from pengajuan.models import Pengajuan

from .forms import PengajuanForm, ProfileForm


@role_required(User.Role.WARGA)
def dashboard(request):
    warga = request.user.warga_profile
    pengajuan = warga.pengajuan_list.all()
    return render(request, "warga/dashboard.html", {
        "jumlah_pengajuan": pengajuan.count(),
        "jumlah_menunggu": pengajuan.filter(
            status__in=[
                Pengajuan.Status.MENUNGGU_VERIFIKASI_DESIL,
                Pengajuan.Status.REKOMENDASI_TERSEDIA,
            ]
        ).count(),
        "jumlah_disetujui": pengajuan.filter(status=Pengajuan.Status.DISETUJUI).count(),
        "jumlah_ditolak": pengajuan.filter(status=Pengajuan.Status.DITOLAK).count(),
        "pengajuan_terbaru": pengajuan.select_related("jenis_bantuan").order_by("-tanggal_pengajuan")[:5],
    })


@role_required(User.Role.WARGA)
def ajukan_bantuan(request):
    """FR-02: warga mengajukan bantuan (jumlah tanggungan, penghasilan,
    jenis bantuan). NIK/RT/RW otomatis dari profil, desil dikosongkan
    (None) sampai validator mengisinya di Tahap 5."""
    warga = request.user.warga_profile

    if request.method == "POST":
        form = PengajuanForm(request.POST)
        if form.is_valid():
            jenis_bantuan = form.cleaned_data["jenis_bantuan"]
            jumlah_tanggungan = form.cleaned_data["jumlah_tanggungan"]
            penghasilan = form.cleaned_data["penghasilan"]

            pengajuan_terdahulu = Pengajuan.objects.filter(
                warga=warga,
                jenis_bantuan=jenis_bantuan,
            ).order_by("-tanggal_pengajuan").first()

            if pengajuan_terdahulu and (
                pengajuan_terdahulu.jumlah_tanggungan != jumlah_tanggungan
                or pengajuan_terdahulu.penghasilan != penghasilan
            ):
                form.add_error(
                    "jenis_bantuan",
                    "Data yang Anda masukkan tidak sesuai dengan data yang pernah diajukan sebelumnya. Silakan gunakan data yang sama.",
                )
                messages.error(
                    request,
                    "Data yang Anda masukkan tidak sesuai dengan data yang pernah diajukan sebelumnya. Silakan gunakan data yang sama.",
                )
            else:
                pengajuan = form.save(commit=False)
                pengajuan.warga = warga
                pengajuan.status = Pengajuan.Status.MENUNGGU_VERIFIKASI_DESIL
                pengajuan.save()
                messages.success(request, "Pengajuan berhasil dikirim. Menunggu verifikasi dari validator kelurahan.")
                return redirect("warga:riwayat")
    else:
        form = PengajuanForm()

    return render(request, "warga/ajukan_bantuan.html", {"form": form})


@role_required(User.Role.WARGA)
def riwayat_pengajuan(request):
    """FR-04: warga melihat status pengajuan. TIDAK menampilkan
    hasil_prediksi/rekomendasi ML sama sekali -- lihat detail_pengajuan.py
    dan template terkait, field itu memang tidak pernah di-query di sini."""
    warga = request.user.warga_profile
    daftar_pengajuan = warga.pengajuan_list.select_related("jenis_bantuan").order_by("-tanggal_pengajuan")
    return render(request, "warga/riwayat.html", {"daftar_pengajuan": daftar_pengajuan})


@role_required(User.Role.WARGA)
def detail_pengajuan(request, pk):
    warga = request.user.warga_profile
    # get_object_or_404 dengan filter warga=warga: warga lain tidak bisa
    # buka detail pengajuan milik warga lain lewat tebak-tebak URL id.
    pengajuan = get_object_or_404(
        Pengajuan.objects.select_related("jenis_bantuan", "verifikasi"),
        pk=pk,
        warga=warga,
    )
    return render(request, "warga/detail_pengajuan.html", {"pengajuan": pengajuan})


@role_required(User.Role.WARGA)
def profile(request):
    warga = request.user.warga_profile
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=warga)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil berhasil diperbarui.")
            return redirect("warga:profile")
    else:
        form = ProfileForm(instance=warga)
    return render(request, "warga/profile.html", {"warga": warga, "form": form})


@role_required(User.Role.WARGA)
def notifications(request):
    warga = request.user.warga_profile
    pengajuan_list = warga.pengajuan_list.select_related("jenis_bantuan", "verifikasi").order_by(
        "-tanggal_pengajuan"
    )
    daftar_notifikasi = [{
        "icon": "bi-check-circle-fill" if pengajuan.status == Pengajuan.Status.DISETUJUI
        else "bi-x-circle-fill" if pengajuan.status == Pengajuan.Status.DITOLAK
        else "bi-hourglass-split",
        "tone": "success" if pengajuan.status == Pengajuan.Status.DISETUJUI
        else "danger" if pengajuan.status == Pengajuan.Status.DITOLAK
        else "waiting",
        "title": (
            f"Pengajuan {pengajuan.jenis_bantuan.nama_bantuan} telah disetujui."
            if pengajuan.status == Pengajuan.Status.DISETUJUI
            else f"Pengajuan {pengajuan.jenis_bantuan.nama_bantuan} ditolak."
            if pengajuan.status == Pengajuan.Status.DITOLAK
            else f"Pengajuan {pengajuan.jenis_bantuan.nama_bantuan} sedang diproses."
        ),
        "date": pengajuan.verifikasi.tanggal_verifikasi if pengajuan.status in (
            Pengajuan.Status.DISETUJUI, Pengajuan.Status.DITOLAK
        ) and hasattr(pengajuan, "verifikasi") else pengajuan.tanggal_pengajuan,
        "detail_url": "warga:detail_pengajuan",
        "pk": pengajuan.pk,
    } for pengajuan in pengajuan_list]

    daftar_notifikasi.append({
        "icon": "bi-person-check-fill",
        "tone": "info",
        "title": "Akun warga Anda berhasil didaftarkan.",
        "date": request.user.date_joined,
        "detail_url": "warga:profile",
        "pk": None,
    })
    daftar_notifikasi.sort(key=lambda item: item["date"], reverse=True)
    return render(request, "warga/notifications.html", {"daftar_notifikasi": daftar_notifikasi})
