# Generated by Django 4.0.6 on 2023-02-11 14:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0032_remove_pricing_trial_period_pricing_free_features_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='subscription',
            old_name='code',
            new_name='reference',
        ),
    ]