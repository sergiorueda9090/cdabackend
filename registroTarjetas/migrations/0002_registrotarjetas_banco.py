# Generated by Django 4.2 on 2025-02-11 00:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registroTarjetas', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='registrotarjetas',
            name='banco',
            field=models.TextField(blank=True, null=True),
        ),
    ]
