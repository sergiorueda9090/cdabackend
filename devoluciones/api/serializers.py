from rest_framework import serializers
from devoluciones.models import Devoluciones

class DevolucionesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Devoluciones
        fields = '__all__'