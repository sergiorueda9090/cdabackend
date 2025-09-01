from rest_framework import serializers
from tarjetastrasladofondo.models import Tarjetastrasladofondo

class TarjetastrasladofondoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tarjetastrasladofondo
        fields = '__all__'