# Generated by Django 4.2 on 2025-04-04 15:54

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('cotizador', '0007_alter_cotizador_idbanco'),
    ]

    operations = [
        migrations.AddField(
            model_name='cotizador',
            name='fechaTramite',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
