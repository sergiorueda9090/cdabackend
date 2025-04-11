
from rest_framework     import serializers
from proveedores.models import Proveedor

class ProveedorSerializer(serializers.ModelSerializer):
    etiqueta_nombre = serializers.CharField(source="etiqueta.nombre", read_only=True)  # Agregar el nombre de la etiqueta
    color = serializers.CharField(source="etiqueta.color", read_only=True)  # Agregar el nombre de la etiqueta

    class Meta:
        model = Proveedor
        fields = '__all__'
        extra_fields = ['etiqueta_nombre','color']

    def validate_nombre(self, value):
        if len(value.strip()) == 0:
            raise serializers.ValidationError("El nombre no puede estar vacío.")
        return value
