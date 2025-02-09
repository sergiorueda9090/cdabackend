# cuentas_bancarias/api/serializers.py
from rest_framework import serializers
from cuentasbancarias.models import CuentaBancaria

class CuentaBancariaSerializer(serializers.ModelSerializer):
    class Meta:
        model = CuentaBancaria
        fields = '__all__'