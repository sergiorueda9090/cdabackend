from rest_framework import serializers
from utilidadocacional.models import Utilidadocacional

class UtilidadocacionalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Utilidadocacional
        fields = '__all__'