# Generated by Django 4.1 on 2023-06-06 11:19

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0062_alter_wallet_meta'),
    ]

    operations = [
        migrations.AddField(
            model_name='pricing',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]