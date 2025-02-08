from rest_framework import serializers
from ..models import Cliente, PrecioLey


class PrecioLeySerializer(serializers.ModelSerializer):
    class Meta:
        model = PrecioLey
        fields = ['id', 'descripcion', 'precio_ley', 'comision', 'fecha']


class ClienteSerializer(serializers.ModelSerializer):
    precios_ley = PrecioLeySerializer(many=True, required=False)

    class Meta:
        model = Cliente
        fields = ['id', 'nombre', 'apellidos', 'telefono', 'direccion', 'fecha_creacion', 'precios_ley', 'color']
