# Generated by Django 4.1 on 2023-03-14 07:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0044_alter_useraccount_country'),
    ]

    operations = [
        migrations.AddField(
            model_name='useraccount',
            name='facebook_handle',
            field=models.CharField(default='', max_length=22),
        ),
        migrations.AddField(
            model_name='useraccount',
            name='instagram_handle',
            field=models.CharField(default='', max_length=22),
        ),
        migrations.AddField(
            model_name='useraccount',
            name='twitter_handle',
            field=models.CharField(default='', max_length=22),
        ),
    ]