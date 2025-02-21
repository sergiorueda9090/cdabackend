from rest_framework import serializers
from gastosgenerales.models import Gastogenerales

class GastogeneralesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gastogenerales
        fields = '__all__'