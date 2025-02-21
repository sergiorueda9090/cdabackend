from rest_framework import serializers
from gastos.models import Gastos

class GastosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gastos
        fields = '__all__'