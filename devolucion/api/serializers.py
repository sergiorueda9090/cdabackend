from rest_framework import serializers
from devolucion.models import Devolucion

class DevolucionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Devolucion
        fields = '__all__'