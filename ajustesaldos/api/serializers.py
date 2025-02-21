from rest_framework      import serializers
from ajustesaldos.models import Ajustesaldo

class AjustesaldoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ajustesaldo
        fields = '__all__'