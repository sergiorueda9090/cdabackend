# Generated by Django 4.2 on 2025-01-25 00:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tramites', '0006_logtramite_idtramite'),
    ]

    operations = [
        migrations.AddField(
            model_name='logtramite',
            name='campo',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
    ]
