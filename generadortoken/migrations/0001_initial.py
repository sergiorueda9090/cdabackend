# Generated by Django 4.2 on 2025-01-26 16:08

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='GeneradorToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('identificacion', models.CharField(max_length=20, verbose_name='Número de Identificación')),
                ('token', models.CharField(max_length=6, verbose_name='Token Generado')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')),
            ],
        ),
    ]
