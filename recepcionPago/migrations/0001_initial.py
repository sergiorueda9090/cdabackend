# Generated by Django 4.2 on 2025-02-18 16:10

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('clientes', '0003_alter_cliente_nombre'),
        ('registroTarjetas', '0003_alter_registrotarjetas_saldo'),
    ]

    operations = [
        migrations.CreateModel(
            name='RecepcionPago',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_ingreso', models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name='Fecha de Ingreso')),
                ('fecha_transaccion', models.DateField(verbose_name='Fecha de Transacción')),
                ('valor', models.TextField(verbose_name='Valor')),
                ('observacion', models.TextField(blank=True, null=True, verbose_name='Observación')),
                ('cliente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='clientes.cliente', verbose_name='Cliente')),
                ('id_tarjeta_bancaria', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='registroTarjetas.registrotarjetas', verbose_name='RegistroTarjetas')),
            ],
            options={
                'verbose_name': 'Recepción de Pago',
                'verbose_name_plural': 'Recepciones de Pago',
            },
        ),
    ]
