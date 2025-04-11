# Generated by Django 4.2 on 2025-04-11 06:25

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('cotizador', '0009_cotizador_sendtoarchivo'),
        ('proveedores', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='FinalProveedor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comisionproveedor', models.CharField(max_length=100)),
                ('fechaCreacion', models.DateTimeField(default=django.utils.timezone.now)),
                ('idcotizador', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cotizador.cotizador')),
                ('idproveedor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='proveedores.proveedor')),
            ],
        ),
    ]
