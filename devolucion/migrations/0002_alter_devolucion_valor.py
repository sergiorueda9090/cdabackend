# Generated by Django 4.2 on 2025-02-18 14:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('devolucion', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='devolucion',
            name='valor',
            field=models.TextField(verbose_name='Valor'),
        ),
    ]
