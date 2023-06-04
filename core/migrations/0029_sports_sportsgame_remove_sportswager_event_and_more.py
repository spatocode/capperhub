# Generated by Django 4.1 on 2023-03-09 12:24

import core.models.games
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0028_transaction_last_update_useraccount_last_updated_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Sports',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='SportsGame',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('competition', models.CharField(max_length=100)),
                ('home', models.CharField(max_length=100)),
                ('away', models.CharField(max_length=100)),
                ('match_day', models.DateTimeField()),
                ('result', models.CharField(max_length=10, null=True)),
                ('time_added', models.DateTimeField(auto_now_add=True)),
                ('markets', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=50), default=core.models.games.default_markets, size=None)),
                ('is_played', models.BooleanField(default=False)),
                ('type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='sports_game', to='core.sports')),
            ],
        ),
        migrations.RemoveField(
            model_name='sportswager',
            name='event',
        ),
        migrations.DeleteModel(
            name='SportsEvent',
        ),
        migrations.AddField(
            model_name='sportswager',
            name='game',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='core.sportsgame'),
        ),
    ]
