# Generated by Django 4.0.6 on 2023-02-11 22:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0033_rename_code_subscription_reference'),
    ]

    operations = [
        migrations.AlterField(
            model_name='matchtips',
            name='game',
            field=models.CharField(max_length=20),
        ),
        migrations.AlterField(
            model_name='matchtips',
            name='league',
            field=models.CharField(max_length=50),
        ),
    ]
