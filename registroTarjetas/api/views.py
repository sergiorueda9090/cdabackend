# cuentas_bancarias/api/views.py
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from registroTarjetas.models import RegistroTarjetas
from .serializers import RegistroTarjetasSerializer

from recepcionPago.models     import RecepcionPago
from devoluciones.models      import Devoluciones
from gastosgenerales.models   import Gastogenerales
from utilidadocacional.models import Utilidadocacional

from django.db.models import Sum

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

@api_view(['GET'])
def obtener_tarjetas_total(request):
    # Verificar si todas las tablas existen antes de ejecutar consultas
    required_models = {
        "RegistroTarjetas": RegistroTarjetas,
        "RecepcionPago": RecepcionPago,
        "Devoluciones": Devoluciones,
        "Gastogenerales": Gastogenerales,
        "Utilidadocacional": Utilidadocacional
    }

    missing_tables = [name for name, model in required_models.items() if not model._meta.db_table]

    if missing_tables:
        return Response(
            {"error": "Algunas tablas no existen en la base de datos", "tablas_faltantes": missing_tables},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    cuentas     = RegistroTarjetas.objects.all()
    #total_recepcion_pagos = RecepcionPago.objects.filter(cuentas[0].id)

    serializer  = RegistroTarjetasSerializer(cuentas, many=True)

    for i in range(len(serializer.data)):
        rtaRecepcionPago = RecepcionPago.objects.filter(
            id_tarjeta_bancaria=serializer.data[i]['id']
        ).aggregate(total_suma=Sum('valor'))

        rtaDevoluciones = Devoluciones.objects.filter(
            id_tarjeta_bancaria=serializer.data[i]['id']
        ).aggregate(total_suma=Sum('valor'))


        rtaGastogenerales = Gastogenerales.objects.filter(
            id_tarjeta_bancaria=serializer.data[i]['id']
        ).aggregate(total_suma=Sum('valor'))

        rtaUtilidadocacional = Utilidadocacional.objects.filter(
            id_tarjeta_bancaria=serializer.data[i]['id']
        ).aggregate(total_suma=Sum('valor'))

        rtaRecepcionPago['total_suma']      = rtaRecepcionPago['total_suma']     if rtaRecepcionPago['total_suma']      is not None else 0
        rtaDevoluciones['total_suma']       = rtaDevoluciones['total_suma']      if rtaDevoluciones['total_suma']       is not None else 0
        rtaGastogenerales['total_suma']     = rtaGastogenerales['total_suma']    if rtaGastogenerales['total_suma']     is not None else 0
        rtaUtilidadocacional['total_suma']  = rtaUtilidadocacional['total_suma'] if rtaUtilidadocacional['total_suma']  is not None else 0

    
        print("rtaRecepcionPago : {}\nrtaDevoluciones: {}\nrtaGastogenerales: {}\nrtaUtilidadocacional: {}"
            .format(rtaRecepcionPago, rtaDevoluciones, rtaGastogenerales, rtaUtilidadocacional))
    
        serializer.data[i]['valor'] = rtaRecepcionPago['total_suma']

    return Response(serializer.data, status=status.HTTP_200_OK)