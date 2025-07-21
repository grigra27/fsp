# Generated migration for model optimizations

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('price', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='apicalllog',
            name='api_name',
            field=models.CharField(db_index=True, max_length=50),
        ),
        migrations.AlterField(
            model_name='apicalllog',
            name='error_message',
            field=models.TextField(blank=True, max_length=500),
        ),
        migrations.AlterField(
            model_name='apicalllog',
            name='success',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AlterField(
            model_name='apicalllog',
            name='timestamp',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='apicalllog',
            name='url',
            field=models.URLField(max_length=500),
        ),
        migrations.AddIndex(
            model_name='apicalllog',
            index=models.Index(fields=['-timestamp', 'success'], name='price_apica_timesta_idx'),
        ),
        migrations.AddIndex(
            model_name='apicalllog',
            index=models.Index(fields=['api_name', '-timestamp'], name='price_apica_api_nam_idx'),
        ),
    ]