# Generated by Django 4.2 on 2024-12-10 07:02

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0004_alter_usermodel_managers'),
    ]

    operations = [
        migrations.CreateModel(
            name='BlacklistedAccessToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(max_length=500, unique=True)),
                ('blacklisted_at', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
    ]
