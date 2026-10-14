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
- `data/dataset.csv` - dataset simulasi 1.000 baris untuk training
  model ML (lihat catatan di bawah)

## Tentang data/dataset.csv

Dataset simulasi, BUKAN data asli warga. Dataset berisi 300 baris awal dan
700 baris simulasi tambahan yang dibuat secara pseudorandom dengan seed
`20261014`; baris awal dipertahankan. Distribusi akhir: 733 `Diterima` dan
267 `Ditolak`. Kolom: `desil`, `jumlah_tanggungan`, `penghasilan`, `status`
(Diterima/Ditolak). Karena baris tambahan dan labelnya sintetis, metrik hasil
training hanya untuk demonstrasi teknis dan bukan bukti performa pada warga
nyata. Ganti dengan data historis asli kelurahan (setelah dianonimkan) dan
evaluasi pada data terpisah sebelum menarik kesimpulan penggunaan lapangan.
