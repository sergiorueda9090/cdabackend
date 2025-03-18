# cuentas_bancarias/api/views.py
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from registroTarjetas.models import RegistroTarjetas
from .serializers import RegistroTarjetasSerializer

from cuentasbancarias.models  import CuentaBancaria
from recepcionPago.models     import RecepcionPago
from devoluciones.models      import Devoluciones
from gastosgenerales.models   import Gastogenerales
from utilidadocacional.models import Utilidadocacional

from django.db import models
from django.db.models import Sum, F, Value
from django.db.models.functions import Replace, Cast

from rest_framework.permissions import IsAuthenticated

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_tarjetas(request):
    cuentas     = RegistroTarjetas.objects.all()
    serializer  = RegistroTarjetasSerializer(cuentas, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_tarjeta(request, id):
    try:
        cuenta = RegistroTarjetas.objects.get(id=id)
        serializer = RegistroTarjetasSerializer(cuenta)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except RegistroTarjetas.DoesNotExist:
        return Response({"error": "Cuenta bancaria no encontrada"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crear_tarjeta(request):
    serializer = RegistroTarjetasSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
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
@permission_classes([IsAuthenticated])
def eliminar_tarjeta(request, id):
    try:
        cuenta = RegistroTarjetas.objects.get(id=id)
        cuenta.delete()
        return Response({"message": "Cuenta bancaria eliminada correctamente"}, status=status.HTTP_204_NO_CONTENT)
    except RegistroTarjetas.DoesNotExist:
        return Response({"error": "Cuenta bancaria no encontrada"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
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
    print(serializer.data)
    
    for i in range(len(serializer.data)):
        
        rtaCuentaBancaria = CuentaBancaria.objects.filter(
            idBanco=serializer.data[i]['id']
        ).aggregate(
            total_suma=Sum(
                Cast(Replace(F('valor'), Value('.'), Value('')), output_field=models.IntegerField())
            )
        )

        rtaRecepcionPago = RecepcionPago.objects.filter(
            id_tarjeta_bancaria=serializer.data[i]['id']
        ).aggregate(
            total_suma=Sum(
                Cast(Replace(F('valor'), Value('.'), Value('')), output_field=models.IntegerField())
            )
        )

        rtaDevoluciones = Devoluciones.objects.filter(
            id_tarjeta_bancaria=serializer.data[i]['id']
        ).aggregate(
            total_suma=Sum(
                Cast(Replace(F('valor'), Value('.'), Value('')), output_field=models.IntegerField())
            )
        )

        rtaGastogenerales = Gastogenerales.objects.filter(
            id_tarjeta_bancaria=serializer.data[i]['id']
        ).aggregate(
            total_suma=Sum(
                Cast(Replace(F('valor'), Value('.'), Value('')), output_field=models.IntegerField())
            )
        )

        rtaUtilidadocacional = Utilidadocacional.objects.filter(
            id_tarjeta_bancaria=serializer.data[i]['id']
        ).aggregate(
            total_suma=Sum(
                Cast(Replace(F('valor'), Value('.'), Value('')), output_field=models.IntegerField())
            )
        )

        rtaCuentaBancaria['total_suma']      = rtaCuentaBancaria['total_suma']     if rtaCuentaBancaria['total_suma']      is not None else 0
        rtaRecepcionPago['total_suma']      = rtaRecepcionPago['total_suma']     if rtaRecepcionPago['total_suma']      is not None else 0
        rtaDevoluciones['total_suma']       = rtaDevoluciones['total_suma']      if rtaDevoluciones['total_suma']       is not None else 0
        rtaGastogenerales['total_suma']     = rtaGastogenerales['total_suma']    if rtaGastogenerales['total_suma']     is not None else 0
        rtaUtilidadocacional['total_suma']  = rtaUtilidadocacional['total_suma'] if rtaUtilidadocacional['total_suma']  is not None else 0

        total_general = (
            rtaCuentaBancaria['total_suma'] +
            rtaRecepcionPago['total_suma'] +
            rtaDevoluciones['total_suma'] +
            rtaGastogenerales['total_suma'] +
            rtaUtilidadocacional['total_suma']
        )
        print("rtaRecepcionPago : {}\nrtaDevoluciones: {}\nrtaGastogenerales: {}\nrtaUtilidadocacional: {}\ntotal_general: {}"
            .format(rtaRecepcionPago, rtaDevoluciones, rtaGastogenerales, rtaUtilidadocacional, total_general))
    
        serializer.data[i]['valor'] = total_general

    return Response(serializer.data, status=status.HTTP_200_OK)