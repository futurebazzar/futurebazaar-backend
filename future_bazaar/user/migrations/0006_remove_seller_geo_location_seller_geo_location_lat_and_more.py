# Generated by Django 4.2.17 on 2024-12-13 18:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0005_blacklistedaccesstoken'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='seller',
            name='geo_location',
        ),
        migrations.AddField(
            model_name='seller',
            name='geo_location_lat',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='seller',
            name='geo_location_lng',
            field=models.FloatField(blank=True, null=True),
        ),
    ]