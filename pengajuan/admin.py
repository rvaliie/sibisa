from django.contrib import admin
from .models import Warga, JenisBantuan, Pengajuan, HasilPrediksi, Verifikasi, DataHistoris

admin.site.register(Warga)
admin.site.register(JenisBantuan)
admin.site.register(Pengajuan)
admin.site.register(HasilPrediksi)
admin.site.register(Verifikasi)
admin.site.register(DataHistoris)
