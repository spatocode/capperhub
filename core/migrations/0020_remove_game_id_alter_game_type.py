# Generated by Django 4.0.6 on 2022-12-27 11:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_remove_wallet_bank_code_useraccount_wallet_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='game',
            name='id',
        ),
        migrations.AlterField(
            model_name='game',
            name='type',
            field=models.CharField(max_length=30, primary_key=True, serialize=False),
        ),
    ]