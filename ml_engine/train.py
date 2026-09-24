"""
Training pipeline Tahap 6-7:
Dataset historis -> preprocessing -> train-test split -> training beberapa
kandidat model -> evaluasi -> pilih model terbaik BERDASARKAN HASIL EVALUASI
(bukan diasumsikan Decision Tree otomatis menang) -> simpan model.

Dijalankan lewat: python manage.py train_model
(lihat pengajuan/management/commands/train_model.py)
"""
import json
from pathlib import Path

import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

from .preprocessing import load_dataset, split_features_target

MODEL_DIR = Path(__file__).resolve().parent / "saved_model"
MODEL_PATH = MODEL_DIR / "model.joblib"
METRICS_PATH = MODEL_DIR / "metrics.json"

# Dataset dummy kita imbalance (~73% Diterima / 27% Ditolak), jadi semua
# kandidat dikasih class_weight="balanced" supaya model tidak cuma
# "malas" menebak Diterima terus demi accuracy tinggi.
CANDIDATES = {
    "decision_tree": Pipeline([
        ("clf", DecisionTreeClassifier(max_depth=4, class_weight="balanced", random_state=42)),
    ]),
    "logistic_regression": Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(class_weight="balanced", random_state=42, max_iter=1000)),
    ]),
    "random_forest": Pipeline([
        ("clf", RandomForestClassifier(n_estimators=200, max_depth=5, class_weight="balanced", random_state=42)),
    ]),
}


def evaluate(pipeline, X_test, y_test) -> dict:
    y_pred = pipeline.predict(X_test)
    cm = confusion_matrix(y_test, y_pred).tolist()
    return {
        "accuracy": round(accuracy_score(y_test, y_pred), 4),
        "precision": round(precision_score(y_test, y_pred, zero_division=0), 4),
        "recall": round(recall_score(y_test, y_pred, zero_division=0), 4),
        "f1_score": round(f1_score(y_test, y_pred, zero_division=0), 4),
        "confusion_matrix": cm,  # [[TN, FP], [FN, TP]]
    }


def main():
    df = load_dataset()
    X, y = split_features_target(df)

    print(f"[train] Total data: {len(df)} | Diterima: {y.sum()} | Ditolak: {len(y) - y.sum()}")

    # stratify=y: proporsi kelas di data train & test dijaga tetap mirip,
    # penting karena datanya imbalance.
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    all_metrics = {}
    fitted_pipelines = {}

    for name, pipeline in CANDIDATES.items():
        pipeline.fit(X_train, y_train)
        metrics = evaluate(pipeline, X_test, y_test)
        all_metrics[name] = metrics
        fitted_pipelines[name] = pipeline
        print(f"\n[train] === {name} ===")
        for k, v in metrics.items():
            print(f"  {k}: {v}")

    # Model terbaik dipilih berdasarkan F1-score (bukan accuracy), karena
    # dataset imbalance -- accuracy tinggi bisa menipu kalau model cuma
    # menebak kelas mayoritas terus. F1 menyeimbangkan precision & recall.
    best_name = max(all_metrics, key=lambda n: all_metrics[n]["f1_score"])
    best_pipeline = fitted_pipelines[best_name]

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump({"pipeline": best_pipeline, "model_name": best_name}, MODEL_PATH)

    with open(METRICS_PATH, "w") as f:
        json.dump({"selected_model": best_name, "all_candidates": all_metrics}, f, indent=2)

    print(f"\n[train] Model terpilih: {best_name} (F1={all_metrics[best_name]['f1_score']})")
    print(f"[train] Model disimpan ke: {MODEL_PATH}")
    return best_name, all_metrics


if __name__ == "__main__":
    main()
