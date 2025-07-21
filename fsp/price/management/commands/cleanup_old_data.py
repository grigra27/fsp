from django.core.management.base import BaseCommand
from django.utils import timezone
from price.models import PriceSnapshot, APICallLog
import datetime
import logging

logger = logging.getLogger('price')


class Command(BaseCommand):
    help = 'Clean up old price snapshots and API call logs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Keep data for this many days (default: 90)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        cutoff_date = timezone.now() - datetime.timedelta(days=days)
        
        # Count old records
        old_snapshots = PriceSnapshot.objects.filter(timestamp__lt=cutoff_date)
        old_api_logs = APICallLog.objects.filter(timestamp__lt=cutoff_date)
        
        snapshot_count = old_snapshots.count()
        api_log_count = old_api_logs.count()
        
        self.stdout.write(f'Found {snapshot_count} old snapshots')
        self.stdout.write(f'Found {api_log_count} old API logs')
        self.stdout.write(f'Cutoff date: {cutoff_date}')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN - No data will be deleted')
            )
            return
        
        if snapshot_count == 0 and api_log_count == 0:
            self.stdout.write('No old data to clean up')
            return
        
        # Delete old records
        try:
            deleted_snapshots, _ = old_snapshots.delete()
            deleted_api_logs, _ = old_api_logs.delete()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully deleted {deleted_snapshots} snapshots '
                    f'and {deleted_api_logs} API logs'
                )
            )
            
        except Exception as e:
            logger.error(f'Error in cleanup_old_data command: {e}')
            self.stdout.write(
                self.style.ERROR(f'Error during cleanup: {e}')
            )