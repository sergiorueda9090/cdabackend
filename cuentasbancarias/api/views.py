# cuentas_bancarias/api/views.py
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from cuentasbancarias.models import CuentaBancaria
from .serializers import CuentaBancariaSerializer

@api_view(['GET'])
def obtener_cuentas(request):
    cuentas     = CuentaBancaria.objects.all()
    serializer  = CuentaBancariaSerializer(cuentas, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
def obtener_cuenta(request, id):
    try:
        cuenta = CuentaBancaria.objects.get(id=id)
        serializer = CuentaBancariaSerializer(cuenta)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except CuentaBancaria.DoesNotExist:
        return Response({"error": "Cuenta bancaria no encontrada"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def crear_cuenta(request):
    serializer = CuentaBancariaSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
def actualizar_cuenta(request, id):
    try:
        cuenta = CuentaBancaria.objects.get(id=id)
    except CuentaBancaria.DoesNotExist:
        return Response({"error": "Cuenta bancaria no encontrada"}, status=status.HTTP_404_NOT_FOUND)

    serializer = CuentaBancariaSerializer(cuenta, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
def eliminar_cuenta(request, id):
    try:
        cuenta = CuentaBancaria.objects.get(id=id)
        cuenta.delete()
        return Response({"message": "Cuenta bancaria eliminada correctamente"}, status=status.HTTP_204_NO_CONTENT)
    except CuentaBancaria.DoesNotExist:
        return Response({"error": "Cuenta bancaria no encontrada"}, status=status.HTTP_404_NOT_FOUND)
