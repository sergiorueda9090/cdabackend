# cuentas_bancarias/api/serializers.py
from rest_framework import serializers
from registroTarjetas.models import RegistroTarjetas

class RegistroTarjetasSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistroTarjetas
        fields = '__all__'