from rest_framework import serializers
from cargosnoregistrados.models import Cargosnodesados

class CargosNoRegistradosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cargosnodesados
        fields = '__all__'