# Generated by Django 4.1 on 2023-03-24 16:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0053_alter_currency_country_alter_pricing_amount_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='useraccount',
            name='image',
            field=models.ImageField(null=True, upload_to='media'),
        ),
    ]