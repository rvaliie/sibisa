from django.core.management.base import BaseCommand

from pengajuan.models import JenisBantuan

DUMMY_JENIS_BANTUAN = [
    ("Bantuan Pangan", "Bantuan untuk memenuhi kebutuhan pangan pokok warga."),
]


class Command(BaseCommand):
    help = "Mengisi data JenisBantuan dummy supaya form pengajuan warga bisa langsung dites (Tahap 4)."

    def handle(self, *args, **options):
        JenisBantuan.objects.exclude(nama_bantuan="Bantuan Pangan").update(status=False)
        created_count = 0
        for nama, deskripsi in DUMMY_JENIS_BANTUAN:
            obj, created = JenisBantuan.objects.get_or_create(
                nama_bantuan=nama,
                defaults={"deskripsi": deskripsi, "status": True},
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Dibuat: {nama}"))
            else:
                self.stdout.write(f"Sudah ada, dilewati: {nama}")
        self.stdout.write(self.style.SUCCESS(f"Selesai. {created_count} jenis bantuan baru ditambahkan."))
