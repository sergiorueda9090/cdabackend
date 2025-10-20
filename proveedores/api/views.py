from rest_framework             import status
from rest_framework.decorators  import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response    import Response
from django.shortcuts           import get_object_or_404
from proveedores.models         import Proveedor
from .serializers               import ProveedorSerializer
from users.decorators           import check_role

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1,2)
def get_proveedores(request):
    proveedores = Proveedor.objects.all()
    if not proveedores.exists():
        return Response({"message": "No hay proveedores registrados."}, status=status.HTTP_404_NOT_FOUND)
    serializer = ProveedorSerializer(proveedores, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1)
def get_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    serializer = ProveedorSerializer(proveedor)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@check_role(1)
def create_proveedor(request):
    serializer = ProveedorSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@check_role(1)
def update_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    serializer = ProveedorSerializer(proveedor, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@check_role(1)
def delete_proveedor(request, pk):
    proveedor = get_object_or_404(Proveedor, pk=pk)
    proveedor.delete()
    return Response({"message": "Proveedor eliminado correctamente."}, status=status.HTTP_204_NO_CONTENT)
