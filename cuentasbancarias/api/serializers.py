# cuentas_bancarias/api/serializers.py
from rest_framework import serializers
from cuentasbancarias.models import CuentaBancaria

class CuentaBancariaSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    # Se usan alias "fi" y "ft" según la unión
    fecha_ingreso = serializers.DateTimeField(source='fi')
    fecha_transaccion = serializers.DateTimeField(source='ft')
    valor = serializers.CharField()
    descripcion = serializers.CharField()