"""
Test untuk pengajuan app + modul ml_engine (Tahap 6-7). ml_engine bukan
Django app jadi tesnya ditaruh di sini (app yang sudah terdaftar), tapi
cuma mengetes ml_engine secara langsung -- tidak menyentuh model Django
apapun. Jalankan: python manage.py test pengajuan
"""
from django.test import SimpleTestCase, TestCase

from ml_engine import predict
from ml_engine.preprocessing import FEATURES, TARGET, load_dataset, split_features_target
from ml_engine.train import CANDIDATES, evaluate, main as train_main


class PreprocessingTest(SimpleTestCase):
    def test_load_dataset_kolom_lengkap(self):
        df = load_dataset()
        for col in FEATURES + [TARGET]:
            self.assertIn(col, df.columns)
        self.assertGreater(len(df), 0)

    def test_split_features_target_bentuk_benar(self):
        df = load_dataset()
        X, y = split_features_target(df)
        self.assertEqual(list(X.columns), FEATURES)
        self.assertTrue(set(y.unique()).issubset({0, 1}))  # target sudah numerik 0/1
        self.assertEqual(len(X), len(y))


class TrainingTest(SimpleTestCase):
    """Melatih ulang model dalam test untuk memastikan pipeline training
    benar-benar bisa dijalankan ulang tanpa error (bukan cuma test
    struktur file)."""

    def test_training_menghasilkan_metrik_untuk_semua_kandidat(self):
        best_name, all_metrics = train_main()
        self.assertIn(best_name, CANDIDATES.keys())
        for name in CANDIDATES:
            self.assertIn(name, all_metrics)
            for metric_key in ["accuracy", "precision", "recall", "f1_score"]:
                self.assertIn(metric_key, all_metrics[name])
                self.assertGreaterEqual(all_metrics[name][metric_key], 0.0)
                self.assertLessEqual(all_metrics[name][metric_key], 1.0)

    def test_model_terpilih_berdasarkan_f1_tertinggi(self):
        best_name, all_metrics = train_main()
        best_f1 = all_metrics[best_name]["f1_score"]
        for name, metrics in all_metrics.items():
            self.assertLessEqual(metrics["f1_score"], best_f1)


class PredictTest(TestCase):
    """Butuh model.joblib sudah ada (dilatih lewat train_model sebelum
    test ini jalan, atau lewat TrainingTest di atas yang jalan duluan
    secara alfabetis dalam file yang sama)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        train_main()  # pastikan model.joblib selalu ada & terbaru sebelum test prediksi

    def test_predict_mengembalikan_field_yang_benar(self):
        hasil = predict.predict_kelayakan(desil=2, jumlah_tanggungan=5, penghasilan=500000)
        self.assertIn(hasil["prediksi"], [predict.LAYAK, predict.TIDAK_LAYAK])
        self.assertGreaterEqual(hasil["probabilitas"], 0.0)
        self.assertLessEqual(hasil["probabilitas"], 1.0)
        self.assertIn("model_name", hasil)

    def test_predict_warga_miskin_lebih_mungkin_layak(self):
        """Bukan jaminan matematis (model probabilistik), tapi pola umum
        dataset dummy kita: desil rendah + tanggungan banyak + penghasilan
        kecil -> lebih mungkin LAYAK dibanding desil tinggi + tanggungan
        sedikit + penghasilan besar."""
        miskin = predict.predict_kelayakan(desil=1, jumlah_tanggungan=6, penghasilan=400000)
        mampu = predict.predict_kelayakan(desil=10, jumlah_tanggungan=0, penghasilan=6000000)
        self.assertEqual(miskin["prediksi"], predict.LAYAK)
        self.assertEqual(mampu["prediksi"], predict.TIDAK_LAYAK)
