"""
Fungsi prediksi untuk data pengajuan BARU (bukan data historis). Dipanggil
dari validator (Tahap 8), bukan langsung oleh warga. Memakai pipeline yang
sama persis dengan yang dipakai saat training (lewat file .joblib) supaya
tidak ada perbedaan preprocessing antara training dan inference.
"""
from pathlib import Path

import joblib
import pandas as pd

from .preprocessing import FEATURES

MODEL_PATH = Path(__file__).resolve().parent / "saved_model" / "model.joblib"

LAYAK = "LAYAK"
TIDAK_LAYAK = "TIDAK_LAYAK"

_cached = None  # lazy singleton, biar file model cuma dibaca sekali per proses


class ModelBelumDilatih(Exception):
    """Dilempar kalau model.joblib belum ada -- jalankan
    `python manage.py train_model` dulu."""


def _load_model():
    global _cached
    if _cached is None:
        if not MODEL_PATH.exists():
            raise ModelBelumDilatih(
                "Model ML belum dilatih. Jalankan `python manage.py train_model` terlebih dahulu."
            )
        _cached = joblib.load(MODEL_PATH)
    return _cached


def predict_kelayakan(desil: int, jumlah_tanggungan: int, penghasilan: int) -> dict:
    """Input: 3 fitur pengajuan (desil sudah diisi validator, tanggungan &
    penghasilan dari form warga). Output: dict prediksi + probabilitas +
    nama model yang dipakai -- SEMUA hasil dari sini adalah rekomendasi
    awal, bukan keputusan final (itu tetap wewenang validator)."""
    loaded = _load_model()
    pipeline = loaded["pipeline"]
    model_name = loaded["model_name"]

    X_baru = pd.DataFrame([[desil, jumlah_tanggungan, penghasilan]], columns=FEATURES)

    kelas_prediksi = pipeline.predict(X_baru)[0]  # 1 = Diterima, 0 = Ditolak
    proba = pipeline.predict_proba(X_baru)[0]     # [P(kelas=0), P(kelas=1)]

    prediksi_label = LAYAK if kelas_prediksi == 1 else TIDAK_LAYAK
    probabilitas = proba[1] if kelas_prediksi == 1 else proba[0]

    return {
        "prediksi": prediksi_label,
        "probabilitas": round(float(probabilitas), 4),
        "model_name": model_name,
    }
