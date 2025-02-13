# cuentas_bancarias/api/views.py
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from registroTarjetas.models import RegistroTarjetas
from .serializers import RegistroTarjetasSerializer

@api_view(['GET'])
def obtener_tarjetas(request):
    cuentas     = RegistroTarjetas.objects.all()
    serializer  = RegistroTarjetasSerializer(cuentas, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
def obtener_tarjeta(request, id):
    try:
        cuenta = RegistroTarjetas.objects.get(id=id)
        serializer = RegistroTarjetasSerializer(cuenta)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except RegistroTarjetas.DoesNotExist:
        return Response({"error": "Cuenta bancaria no encontrada"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def crear_tarjeta(request):
    serializer = RegistroTarjetasSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
def actualizar_tarjeta(request, id):
    try:
        cuenta = RegistroTarjetas.objects.get(id=id)
    except RegistroTarjetas.DoesNotExist:
        return Response({"error": "Cuenta bancaria no encontrada"}, status=status.HTTP_404_NOT_FOUND)

    serializer = RegistroTarjetasSerializer(cuenta, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
def eliminar_tarjeta(request, id):
    try:
        cuenta = RegistroTarjetas.objects.get(id=id)
        cuenta.delete()
        return Response({"message": "Cuenta bancaria eliminada correctamente"}, status=status.HTTP_204_NO_CONTENT)
    except RegistroTarjetas.DoesNotExist:
        return Response({"error": "Cuenta bancaria no encontrada"}, status=status.HTTP_404_NOT_FOUND)
