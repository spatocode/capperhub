# Generated by Django 4.1 on 2023-03-09 12:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0030_rename_sports_sport_remove_sportswager_currency_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sportsgame',
            name='result',
            field=models.CharField(default='', max_length=10),
        ),
    ]
