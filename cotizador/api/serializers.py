from rest_framework import serializers
from cotizador.models import Cotizador, LogCotizador

class CotizadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cotizador
        fields = '__all__'

class LogCotizadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogCotizador
        fields = '__all__'