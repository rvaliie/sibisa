from django.core.management.base import BaseCommand

from ml_engine.train import main as train_main


class Command(BaseCommand):
    help = "Melatih model klasifikasi kelayakan bansos dari data historis dan menyimpan model terbaik."

    def handle(self, *args, **options):
        train_main()
