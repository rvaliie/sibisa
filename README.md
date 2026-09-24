# SADEKA - Sistem Pendukung Keputusan Kelayakan Penerima Bantuan Sosial

Status: Tahap 2 selesai (struktur project + database). Fitur (auth, warga,
validator, ML) belum diimplementasikan -- menyusul di tahap berikutnya.

## Cara menjalankan (development)

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser  # buat akun admin untuk cek /admin
python manage.py runserver
```

Buka http://127.0.0.1:8000/admin untuk melihat/menambah data lewat Django admin
(sementara belum ada halaman warga/validator, itu Tahap 3-5).

## Struktur app

- `accounts/`  - custom User (role: WARGA / VALIDATOR)
- `pengajuan/` - model inti bersama: Warga, JenisBantuan, Pengajuan,
  HasilPrediksi, Verifikasi, DataHistoris
- `warga/`     - fitur khusus warga (Tahap 4)
- `validator/` - fitur khusus validator (Tahap 5)
- `ml_engine/` - package Python biasa (bukan Django app) untuk
  preprocessing, training, dan prediksi (Tahap 6-7)
- `data/data_historis_dummy.csv` - dataset dummy 300 baris untuk training
  awal model ML (lihat catatan di bawah)

## Tentang data/data_historis_dummy.csv

Dataset simulasi, BUKAN data asli warga. Kolom: `desil`, `jumlah_tanggungan`,
`penghasilan`, `status` (Diterima/Ditolak). Distribusi status sekitar 73%
Diterima / 27% Ditolak -- sengaja tidak seimbang untuk melatih evaluasi model
yang benar (accuracy saja tidak cukup, perlu precision/recall/F1). Ganti
dengan data historis asli kelurahan (setelah dianonimkan) begitu tersedia.
