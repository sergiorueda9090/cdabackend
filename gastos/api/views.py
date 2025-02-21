from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators  import api_view, permission_classes
from rest_framework.response    import Response
from rest_framework             import status
from gastos.models              import Gastos
from .serializers               import GastosSerializer

#Listar todas las devoluciones
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_gastos(request):
    devolucionAll= Gastos.objects.all()
    serializer   = GastosSerializer(devolucionAll, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

#Crear una nueva devolución
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crear_gasto(request):
    required_fields = ["name"]

    # Validar que los campos requeridos estén en la petición
    for field in required_fields:
        if field not in request.data or not request.data[field]:
            return Response({"error": f"El campo '{field}' es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)


    # Crear la devolución
    GastosCreate = Gastos.objects.create(
        name        = request.data["name"],
        observacion = request.data.get("observacion", "")
    )

    serializer = GastosSerializer(GastosCreate)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

#Obtener una devolución por ID
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_gasto(request, pk):
    try:
        gastosGet = Gastos.objects.get(pk=pk)
    except Gastos.DoesNotExist:
        return Response({"error": "Gasto no encontrada."}, status=status.HTTP_404_NOT_FOUND)

    serializer = GastosSerializer(gastosGet)
    return Response(serializer.data, status=status.HTTP_200_OK)

#Actualizar una devolución
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def actualizar_gasto(request, pk):
    try:
        gastosGet = Gastos.objects.get(pk=pk)
    except Gastos.DoesNotExist:
        return Response({"error": "Gastos no encontrada."}, status=status.HTTP_404_NOT_FOUND)

    
    gastosGet.name = request.data.get("name", gastosGet.name)
    gastosGet.observacion = request.data.get("observacion", gastosGet.observacion)

    gastosGet.save()

    serializer = GastosSerializer(gastosGet)
    return Response(serializer.data, status=status.HTTP_200_OK)

#Eliminar una devolución
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def eliminar_gasto(request, pk):
    try:
        GastosDelete = Gastos.objects.get(pk=pk)
        GastosDelete.delete()
        return Response({"mensaje": "Gastos eliminada correctamente."}, status=status.HTTP_204_NO_CONTENT)
    except Gastos.DoesNotExist:
        return Response({"error": "Gastos no encontrada."}, status=status.HTTP_404_NOT_FOUND)
