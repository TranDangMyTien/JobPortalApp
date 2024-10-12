from django.core.management.base import BaseCommand
from jobs.data_analysis import main

class Command(BaseCommand):
    help = 'Runs data analysis for job applications'

    def handle(self, *args, **options):
        main()
