from django.db import models
from django.utils import timezone


class PriceSnapshot(models.Model):
    """Model to store historical price data snapshots"""
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    moex_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    fair_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pb_ratio = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    own_capital = models.BigIntegerField(null=True, blank=True)
    price_score = models.CharField(max_length=50, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Price Snapshot'
        verbose_name_plural = 'Price Snapshots'
    
    def __str__(self):
        return f"Price snapshot at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


class APICallLog(models.Model):
    """Model to log API calls for monitoring"""
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    api_name = models.CharField(max_length=50, db_index=True)  # 'moex', 'cbr', etc.
    url = models.URLField(max_length=500)
    status_code = models.IntegerField(null=True, blank=True)
    response_time_ms = models.IntegerField(null=True, blank=True)
    success = models.BooleanField(default=False, db_index=True)
    error_message = models.TextField(blank=True, max_length=500)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'API Call Log'
        verbose_name_plural = 'API Call Logs'
        indexes = [
            models.Index(fields=['-timestamp', 'success']),
            models.Index(fields=['api_name', '-timestamp']),
        ]
    
    def __str__(self):
        status = "✓" if self.success else "✗"
        return f"{status} {self.api_name} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"