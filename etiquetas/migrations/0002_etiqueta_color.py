# Generated by Django 4.2 on 2025-02-05 23:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('etiquetas', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='etiqueta',
            name='color',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
