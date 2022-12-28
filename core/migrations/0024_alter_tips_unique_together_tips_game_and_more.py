# Generated by Django 4.0.6 on 2022-12-28 13:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0023_game'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='tips',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='tips',
            name='game',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='tips', to='core.game'),
        ),
        migrations.AlterUniqueTogether(
            name='tips',
            unique_together={('game', 'issuer', 'home_team', 'away_team', 'date')},
        ),
    ]
