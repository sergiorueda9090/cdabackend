# Generated by Django 4.2 on 2025-02-11 03:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cuentasbancarias', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='cuentabancaria',
            old_name='nombre_cuenta',
            new_name='fechaIngreso',
        ),
        migrations.RemoveField(
            model_name='cuentabancaria',
            name='imagen',
        ),
        migrations.RemoveField(
            model_name='cuentabancaria',
            name='numero_cuenta',
        ),
        migrations.RemoveField(
            model_name='cuentabancaria',
            name='saldo',
        ),
        migrations.AddField(
            model_name='cuentabancaria',
            name='cilindraje',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='cuentabancaria',
            name='fechaTransaccion',
            field=models.CharField(default=1, max_length=250),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='cuentabancaria',
            name='idBanco',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='cuentabancaria',
            name='idCotizador',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='cuentabancaria',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='comprobantesdepago/'),
        ),
        migrations.AddField(
            model_name='cuentabancaria',
            name='nombreTitular',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='cuentabancaria',
            name='valor',
            field=models.TextField(blank=True, null=True),
        ),
    ]
