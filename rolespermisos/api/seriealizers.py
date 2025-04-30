
from rest_framework.serializers import ModelSerializer
from rolespermisos.models       import Rolespermisos

# Serializador para el modelo Rolespermisos
class RolespermisosSerializer(ModelSerializer):
    class Meta:
        model = Rolespermisos
        fields = '__all__'  # Incluye todos los campos del modelo
