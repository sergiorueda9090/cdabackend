# Generated by Django 4.2 on 2025-01-28 13:13

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Cotizador',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('idUsuario', models.IntegerField()),
                ('idCliente', models.IntegerField()),
                ('etiquetaDos', models.CharField(blank=True, max_length=255, null=True)),
                ('placa', models.CharField(max_length=50)),
                ('cilindraje', models.CharField(max_length=50)),
                ('modelo', models.CharField(max_length=50)),
                ('chasis', models.CharField(max_length=50)),
                ('tipoDocumento', models.CharField(max_length=50)),
                ('numeroDocumento', models.CharField(max_length=50)),
                ('nombreCompleto', models.CharField(max_length=255)),
                ('telefono', models.CharField(blank=True, max_length=20, null=True)),
                ('correo', models.EmailField(blank=True, max_length=254, null=True)),
                ('direccion', models.TextField(blank=True, null=True)),
                ('pagoInmediato', models.TextField(blank=True, null=True)),
                ('linkPago', models.TextField(blank=True, null=True)),
                ('precioDeLey', models.CharField(default='', max_length=255)),
                ('comisionPrecioLey', models.CharField(default='', max_length=255)),
                ('total', models.CharField(default='', max_length=255)),
                ('pdf', models.FileField(blank=True, null=True, upload_to='media/pdfs/')),
                ('fechaCreacion', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
        migrations.CreateModel(
            name='LogCotizador',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('idCotizador', models.IntegerField()),
                ('idUsuario', models.IntegerField()),
                ('idCliente', models.IntegerField()),
                ('accion', models.CharField(choices=[('crear', 'Crear'), ('editar', 'Editar'), ('eliminar', 'Eliminar')], max_length=10)),
                ('campo', models.CharField(blank=True, max_length=250, null=True)),
                ('antiguoValor', models.TextField()),
                ('nuevoValor', models.TextField()),
                ('fecha', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
