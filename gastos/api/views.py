from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators  import api_view, permission_classes
from rest_framework.response    import Response
from rest_framework             import status
from gastos.models              import Gastos
from .serializers               import GastosSerializer

from datetime import datetime
from django.db.models import Q

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

def parse_date_with_defaults(date_str, is_end=False):
    if not date_str:
        return None
    
    parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
    if is_end:
        parsed_date = parsed_date.replace(hour=23, minute=59, second=59)
    else:
        parsed_date = parsed_date.replace(hour=0, minute=0, second=0)
    return parsed_date

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_gastos_filtradas(request):
    fecha_inicio = parse_date_with_defaults(request.GET.get('fechaIncio'))
    fecha_fin    = parse_date_with_defaults(request.GET.get('fechaFin'), is_end=True)

    filtro_fecha = Q()
    if fecha_inicio and fecha_fin:
        filtro_fecha = Q(fecha_ingreso__range=(fecha_inicio, fecha_fin))
    elif fecha_inicio:
        filtro_fecha = Q(fecha_ingreso__gte=fecha_inicio)
    elif fecha_fin:
        filtro_fecha = Q(fecha_ingreso__lte=fecha_fin)

    
    devolucionAll= Gastos.objects.filter(filtro_fecha)

    serializer   = GastosSerializer(devolucionAll, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)