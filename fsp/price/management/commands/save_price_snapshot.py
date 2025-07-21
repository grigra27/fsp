from django.core.management.base import BaseCommand
from price.services import sber_service
import logging

logger = logging.getLogger('price')


class Command(BaseCommand):
    help = 'Save a price snapshot to the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force save even if data is incomplete',
        )

    def handle(self, *args, **options):
        self.stdout.write('Saving price snapshot...')
        
        try:
            snapshot = sber_service.save_snapshot()
            
            if snapshot:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully saved snapshot {snapshot.id} at {snapshot.timestamp}'
                    )
                )
                
                # Display snapshot data
                self.stdout.write(f'MOEX Price: {snapshot.moex_price}')
                self.stdout.write(f'Fair Price: {snapshot.fair_price}')
                self.stdout.write(f'P/B Ratio: {snapshot.pb_ratio}')
                self.stdout.write(f'Price Score: {snapshot.price_score}')
                
            else:
                self.stdout.write(
                    self.style.ERROR('Failed to save snapshot - no data available')
                )
                
        except Exception as e:
            logger.error(f'Error in save_price_snapshot command: {e}')
            self.stdout.write(
                self.style.ERROR(f'Error saving snapshot: {e}')
            )