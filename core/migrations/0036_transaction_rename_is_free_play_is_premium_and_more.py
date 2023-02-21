# Generated by Django 4.0.6 on 2023-02-13 21:15

import core.shared.model_utils
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0035_rename_matchtips_play_delete_bookingcodetips'),
    ]

    operations = [
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.PositiveIntegerField(choices=[(0, 'DEPOSIT'), (1, 'WITHDRAWAL')], editable=False)),
                ('amount', models.IntegerField(default=0, editable=False)),
                ('reference', models.CharField(default=core.shared.model_utils.generate_unique_code, editable=False, max_length=32)),
                ('issuer', models.PositiveIntegerField(choices=[(0, 'PAYSTACK')], editable=False)),
                ('channel', models.PositiveIntegerField(choices=[(0, 'BANK'), (0, 'CARD')], editable=False)),
                ('currency', models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='currency_transaction', to='core.currency')),
                ('user', models.ForeignKey(editable=False, on_delete=django.db.models.deletion.PROTECT, related_name='user_transactions', to='core.useraccount')),
            ],
        ),
        migrations.RenameField(
            model_name='play',
            old_name='is_free',
            new_name='is_premium',
        ),
        migrations.RemoveField(
            model_name='subscription',
            name='payment',
        ),
        migrations.AlterField(
            model_name='subscription',
            name='issuer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='issuer_subscriptions', to='core.useraccount'),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='subscriber',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='subscriber_subscriptions', to='core.useraccount'),
        ),
        migrations.DeleteModel(
            name='Payment',
        ),
    ]