from rest_framework import serializers
from recepcionPago.models import RecepcionPago

class RecepcionPagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecepcionPago
        fields = '__all__'