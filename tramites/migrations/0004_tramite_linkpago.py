# Generated by Django 4.2 on 2025-01-24 01:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tramites', '0003_tramite_tipodocumento'),
    ]

    operations = [
        migrations.AddField(
            model_name='tramite',
            name='linkPago',
            field=models.TextField(blank=True, null=True),
        ),
    ]
