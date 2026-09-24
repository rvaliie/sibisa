from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import role_required
from accounts.models import User
from ml_engine.predict import ModelBelumDilatih, predict_kelayakan
from pengajuan.models import HasilPrediksi, Pengajuan, Verifikasi
from pengajuan.utils import mask_nik

from .forms import DesilForm, KeputusanForm


@role_required(User.Role.VALIDATOR)
def dashboard(request):
    """Menampilkan ringkasan statistik dan maksimal 5 pengajuan terbaru."""
    semua_pengajuan = Pengajuan.objects.all()
    
    # Hitung metrik
    total = semua_pengajuan.count()
    menunggu_desil = semua_pengajuan.filter(status=Pengajuan.Status.MENUNGGU_VERIFIKASI_DESIL).count()
    ada_rekomendasi = semua_pengajuan.filter(status=Pengajuan.Status.REKOMENDASI_TERSEDIA).count()
    disetujui = semua_pengajuan.filter(status=Pengajuan.Status.DISETUJUI).count()
    ditolak = semua_pengajuan.filter(status=Pengajuan.Status.DITOLAK).count()
    
    # Ambil 5 terbaru yang belum selesai
    terbaru = semua_pengajuan.filter(
        status__in=[Pengajuan.Status.MENUNGGU_VERIFIKASI_DESIL, Pengajuan.Status.REKOMENDASI_TERSEDIA]
    ).select_related("warga", "jenis_bantuan").order_by("-tanggal_pengajuan")[:5]

    data_terbaru = [
        {"pengajuan": p, "nik_mask": mask_nik(p.warga.nik)}
        for p in terbaru
    ]

    return render(request, "validator/dashboard.html", {
        "total": total,
        "menunggu_desil": menunggu_desil,
        "ada_rekomendasi": ada_rekomendasi,
        "disetujui": disetujui,
        "ditolak": ditolak,
        "data_terbaru": data_terbaru,
    })


@role_required(User.Role.VALIDATOR)
def data_pengajuan(request):
    """Menampilkan daftar pengajuan aktif yang perlu diproses."""
    daftar_pengajuan = Pengajuan.objects.filter(
        status__in=[Pengajuan.Status.MENUNGGU_VERIFIKASI_DESIL, Pengajuan.Status.REKOMENDASI_TERSEDIA]
    ).select_related("warga", "jenis_bantuan").order_by("-tanggal_pengajuan")

    search = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    jenis_id = request.GET.get("jenis_bantuan", "").strip()
    rt = request.GET.get("rt", "").strip()
    if search:
        daftar_pengajuan = daftar_pengajuan.filter(
            warga__nama__icontains=search
        ) | daftar_pengajuan.filter(warga__nik__icontains=search)
    if status in dict(Pengajuan.Status.choices):
        daftar_pengajuan = daftar_pengajuan.filter(status=status)
    if jenis_id:
        daftar_pengajuan = daftar_pengajuan.filter(jenis_bantuan_id=jenis_id)
    if rt:
        daftar_pengajuan = daftar_pengajuan.filter(warga__rt=rt)
    
    data = [
        {"pengajuan": p, "nik_mask": mask_nik(p.warga.nik)}
        for p in daftar_pengajuan
    ]
    return render(request, "validator/data_pengajuan.html", {
        "data": data,
        "status_choices": Pengajuan.Status.choices,
        "jenis_bantuan_list": Pengajuan.objects.filter(
            status__in=[Pengajuan.Status.MENUNGGU_VERIFIKASI_DESIL, Pengajuan.Status.REKOMENDASI_TERSEDIA]
        ).values_list("jenis_bantuan", "jenis_bantuan__nama_bantuan").distinct(),
        "rt_list": Pengajuan.objects.filter(
            status__in=[Pengajuan.Status.MENUNGGU_VERIFIKASI_DESIL, Pengajuan.Status.REKOMENDASI_TERSEDIA]
        ).values_list("warga__rt", flat=True).distinct().order_by("warga__rt"),
        "search": search,
        "selected_status": status,
        "selected_jenis": jenis_id,
        "selected_rt": rt,
    })


@role_required(User.Role.VALIDATOR)
def riwayat_pengajuan(request):
    """Menampilkan daftar pengajuan yang sudah berstatus selesai."""
    daftar_pengajuan = Pengajuan.objects.filter(
        status__in=[Pengajuan.Status.DISETUJUI, Pengajuan.Status.DITOLAK]
    ).select_related("warga", "jenis_bantuan", "hasil_prediksi", "verifikasi").order_by("-tanggal_pengajuan")

    jenis_id = request.GET.get("jenis_bantuan")
    tanggal_mulai = request.GET.get("tanggal_mulai")
    tanggal_selesai = request.GET.get("tanggal_selesai")
    if jenis_id:
        daftar_pengajuan = daftar_pengajuan.filter(jenis_bantuan_id=jenis_id)
    if tanggal_mulai:
        daftar_pengajuan = daftar_pengajuan.filter(tanggal_pengajuan__date__gte=tanggal_mulai)
    if tanggal_selesai:
        daftar_pengajuan = daftar_pengajuan.filter(tanggal_pengajuan__date__lte=tanggal_selesai)
    
    data = [
        {"pengajuan": p, "nik_mask": mask_nik(p.warga.nik)}
        for p in daftar_pengajuan
    ]
    return render(request, "validator/riwayat.html", {
        "data": data,
        "jenis_bantuan_list": Pengajuan.objects.filter(
            status__in=[Pengajuan.Status.DISETUJUI, Pengajuan.Status.DITOLAK]
        ).values_list("jenis_bantuan", "jenis_bantuan__nama_bantuan").distinct(),
        "selected_jenis": jenis_id or "",
        "tanggal_mulai": tanggal_mulai or "",
        "tanggal_selesai": tanggal_selesai or "",
    })


@role_required(User.Role.VALIDATOR)
def detail_pengajuan(request, pk):
    """FR-07 s.d. FR-12: tampilkan NIK penuh untuk dicek manual di web
    pusat, input desil, jalankan prediksi ML, lalu validator menetapkan
    keputusan akhir (disetujui/ditolak) beserta catatan. Keputusan akhir
    HANYA bisa diambil setelah rekomendasi sistem tersedia -- validator
    tetap mempertimbangkan rekomendasi, tapi keputusannya manual, bukan
    otomatis mengikuti hasil ML."""
    pengajuan = get_object_or_404(Pengajuan.objects.select_related("warga", "jenis_bantuan"), pk=pk)
    desil_form = DesilForm(instance=pengajuan)
    hasil_prediksi = getattr(pengajuan, "hasil_prediksi", None)
    verifikasi = getattr(pengajuan, "verifikasi", None)
    keputusan_form = KeputusanForm(instance=verifikasi)

    if request.method == "POST":
        if "submit_desil" in request.POST:
            desil_form = DesilForm(request.POST, instance=pengajuan)
            if desil_form.is_valid():
                desil_form.save()
                messages.success(request, "Desil berhasil disimpan.")
                return redirect("validator:detail_pengajuan", pk=pengajuan.pk)

        elif "jalankan_prediksi" in request.POST:
            if pengajuan.desil is None:
                messages.error(request, "Isi desil terlebih dahulu sebelum menjalankan prediksi.")
                return redirect("validator:detail_pengajuan", pk=pengajuan.pk)
            try:
                hasil = predict_kelayakan(
                    desil=pengajuan.desil,
                    jumlah_tanggungan=pengajuan.jumlah_tanggungan,
                    penghasilan=pengajuan.penghasilan,
                )
            except ModelBelumDilatih as e:
                messages.error(request, str(e))
                return redirect("validator:detail_pengajuan", pk=pengajuan.pk)

            HasilPrediksi.objects.update_or_create(
                pengajuan=pengajuan,
                defaults={
                    "prediksi": hasil["prediksi"],
                    "probabilitas": hasil["probabilitas"],
                    "model_digunakan": hasil["model_name"],
                },
            )
            # kalau sebelumnya sudah pernah diputuskan lalu desil/prediksi
            # diulang, status dikembalikan ke "rekomendasi tersedia" --
            # keputusan lama TIDAK dihapus otomatis, validator yang
            # memutuskan ulang secara sadar lewat form keputusan di bawah.
            pengajuan.status = Pengajuan.Status.REKOMENDASI_TERSEDIA
            pengajuan.save(update_fields=["status"])
            messages.success(request, "Prediksi berhasil dijalankan. Rekomendasi tersedia di bawah.")
            return redirect("validator:detail_pengajuan", pk=pengajuan.pk)

        elif "submit_keputusan" in request.POST:
            if hasil_prediksi is None:
                messages.error(request, "Jalankan prediksi terlebih dahulu sebelum menetapkan keputusan akhir.")
                return redirect("validator:detail_pengajuan", pk=pengajuan.pk)
            keputusan_form = KeputusanForm(request.POST, instance=verifikasi)
            if keputusan_form.is_valid():
                verif = keputusan_form.save(commit=False)
                verif.pengajuan = pengajuan
                verif.validator = request.user
                verif.save()
                pengajuan.status = (
                    Pengajuan.Status.DISETUJUI
                    if verif.keputusan == Verifikasi.Keputusan.DISETUJUI
                    else Pengajuan.Status.DITOLAK
                )
                pengajuan.save(update_fields=["status"])
                messages.success(request, "Keputusan akhir berhasil disimpan.")
                return redirect("validator:detail_pengajuan", pk=pengajuan.pk)

    return render(request, "validator/detail_pengajuan.html", {
        "pengajuan": pengajuan,
        "form": desil_form,
        "hasil_prediksi": hasil_prediksi,
        "verifikasi": verifikasi,
        "keputusan_form": keputusan_form,
    })
