from rest_framework         import serializers
from fichaproveedor.models  import FichaProveedor
from proveedores.models     import Proveedor
from cotizador.models       import Cotizador

class ProveedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proveedor
        fields = '__all__'  # O especifica los campos necesarios

class CotizadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cotizador
        fields = '__all__'  # O especifica los campos necesarios

class FichaProveedorSerializer(serializers.ModelSerializer):
    idproveedor = ProveedorSerializer(read_only=True)  # Incluir datos del proveedor
    idcotizador = CotizadorSerializer(read_only=True)  # Incluir datos del cotizador

    class Meta:
        model = FichaProveedor
        fields = '__all__'
