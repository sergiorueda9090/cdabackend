from rest_framework import serializers
from tramites.models import Tramite, LogTramite

class TramiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tramite
        fields = '__all__'

class LogTramiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogTramite
        fields = '__all__'