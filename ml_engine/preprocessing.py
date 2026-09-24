"""
Preprocessing dataset historis untuk training model kelayakan bansos.
Sengaja dipisah dari train.py supaya langkah yang sama persis bisa dipakai
ulang saat prediksi data baru di predict.py -- mencegah data leakage akibat
preprocessing yang beda antara training dan inference.
"""
from pathlib import Path

import pandas as pd

FEATURES = ["desil", "jumlah_tanggungan", "penghasilan"]
TARGET = "status"
STATUS_DITERIMA = "Diterima"
STATUS_DITOLAK = "Ditolak"

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "data_historis_dummy.csv"


def load_dataset(csv_path: Path = DATA_PATH) -> pd.DataFrame:
    """Load CSV data historis + pengecekan missing value dasar."""
    df = pd.read_csv(csv_path)

    required_cols = FEATURES + [TARGET]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Kolom wajib tidak ditemukan di dataset: {missing_cols}")

    n_before = len(df)
    df = df.dropna(subset=required_cols)
    n_dropped = n_before - len(df)
    if n_dropped:
        print(f"[preprocessing] {n_dropped} baris dengan missing value dibuang dari {n_before} baris.")

    return df


def split_features_target(df: pd.DataFrame):
    """Pisahkan fitur (X) dan target (y). Target diubah ke 1/0 (bukan string)
    supaya bisa dipakai langsung oleh scikit-learn dan predict_proba."""
    X = df[FEATURES].copy()
    y = (df[TARGET] == STATUS_DITERIMA).astype(int)
    return X, y
