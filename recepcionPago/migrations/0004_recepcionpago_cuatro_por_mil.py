# Generated by Django 4.2 on 2025-05-06 20:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recepcionPago', '0003_alter_recepcionpago_fecha_transaccion'),
    ]

    operations = [
        migrations.AddField(
            model_name='recepcionpago',
            name='cuatro_por_mil',
            field=models.TextField(blank=True, null=True),
        ),
    ]
