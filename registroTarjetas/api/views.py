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
from cotizador.models         import Cotizador
from tarjetastrasladofondo.models import Tarjetastrasladofondo
from cargosnoregistrados.models     import Cargosnodesados

from django.db import models
from django.db.models import Sum, F, Value
from django.db.models.functions import Replace, Cast

from rest_framework.permissions import IsAuthenticated
from users.decorators           import check_role
from django.db import transaction

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1,2)
def obtener_tarjetas(request):
    cuentas     = RegistroTarjetas.objects.all()
    serializer  = RegistroTarjetasSerializer(cuentas, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1,2)
def obtener_tarjeta(request, id):
    try:
        cuenta     = RegistroTarjetas.objects.get(id=id)
        serializer = RegistroTarjetasSerializer(cuenta)

        # 🔥 Aquí llamamos a la función auxiliar
        total = calcular_total_tarjeta(id)

        data = serializer.data
        data["saldo"] = total  # 👉 añadimos el total al response

        return Response(data, status=status.HTTP_200_OK)

    except RegistroTarjetas.DoesNotExist:
        return Response({"error": "Cuenta bancaria no encontrada"}, status=status.HTTP_404_NOT_FOUND)

def calcular_total_tarjeta(tarjeta_id: int) -> int:
    """Calcula el total de una tarjeta en todas las tablas relacionadas."""
    
    def get_total(model, field="id_tarjeta_bancaria"):
        rta = model.objects.filter(**{field: tarjeta_id}).aggregate(
            total_suma=Sum(
                Cast(Replace(F('valor'), Value('.'), Value('')), output_field=models.IntegerField())
            )
        )
        return rta['total_suma'] if rta['total_suma'] is not None else 0

    total_general = (
        get_total(CuentaBancaria, field="idBanco") +
        get_total(RecepcionPago) +
        get_total(Devoluciones) +
        get_total(Gastogenerales) +
        get_total(Utilidadocacional) -
        get_total(Tarjetastrasladofondo, field="id_tarjeta_bancaria_envia") +
        get_total(Tarjetastrasladofondo, field="id_tarjeta_bancaria_recibe")
    )

    return total_general

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@check_role(1,2)
def crear_tarjeta(request):
    serializer = RegistroTarjetasSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@check_role(1,2)
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
@check_role(1,2)
def eliminar_tarjeta(request, id):
    try:
        cuenta = RegistroTarjetas.objects.get(id=id)
        cuenta.delete()
        return Response({"message": "Cuenta bancaria eliminada correctamente"}, status=status.HTTP_204_NO_CONTENT)
    except RegistroTarjetas.DoesNotExist:
        return Response({"error": "Cuenta bancaria no encontrada"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1, 2)
def obtener_tarjetas_total(request):
    # Verificar si todas las tablas existen antes de ejecutar consultas
    required_models = {
        "RegistroTarjetas": RegistroTarjetas,
        "RecepcionPago": RecepcionPago,
        "Devoluciones": Devoluciones,
        "Gastogenerales": Gastogenerales,
        "Utilidadocacional": Utilidadocacional,
        "Tarjetastrasladofondo": Tarjetastrasladofondo,
        "Cargosnodesados": Cargosnodesados
    }

    missing_tables = [
        name for name, model in required_models.items() if not model._meta.db_table
    ]

    if missing_tables:
        return Response(
            {
                "error": "Algunas tablas no existen en la base de datos",
                "tablas_faltantes": missing_tables,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    cuentas     = RegistroTarjetas.objects.all()
    serializer  = RegistroTarjetasSerializer(cuentas, many=True)

    for i in range(len(serializer.data)):
        tarjeta_id = serializer.data[i]['id']

        # Función para sumar valores numéricos
        def sumar_valores(queryset):
            return queryset.aggregate(
                total_suma=Sum(
                    Cast(Replace(F('valor'), Value('.'), Value('')), output_field=models.IntegerField())
                )
            )['total_suma'] or 0

        # Consultas por tarjeta
        rtaCuentaBancaria       = sumar_valores(CuentaBancaria.objects.filter(idBanco=tarjeta_id))
        rtaRecepcionPago        = sumar_valores(RecepcionPago.objects.filter(id_tarjeta_bancaria=tarjeta_id))
        rtaDevoluciones         = sumar_valores(Devoluciones.objects.filter(id_tarjeta_bancaria=tarjeta_id))
        rtaGastogenerales       = sumar_valores(Gastogenerales.objects.filter(id_tarjeta_bancaria=tarjeta_id))
        rtaUtilidadocacional    = sumar_valores(Utilidadocacional.objects.filter(id_tarjeta_bancaria=tarjeta_id))
        rtaTarjetastrasladofondoResta = sumar_valores(Tarjetastrasladofondo.objects.filter(id_tarjeta_bancaria_envia=tarjeta_id))
        rtaTarjetastrasladofondoSuma = sumar_valores(Tarjetastrasladofondo.objects.filter(id_tarjeta_bancaria_recibe=tarjeta_id))
        rtaCargosnodesados = sumar_valores(Cargosnodesados.objects.filter(id_tarjeta_bancaria=tarjeta_id))

        # 🔹 Sumar Cargosnodeseados al total general
        total_general = (
            rtaCuentaBancaria +
            rtaRecepcionPago +
            rtaDevoluciones +
            rtaGastogenerales +
            rtaUtilidadocacional -
            rtaTarjetastrasladofondoResta +
            rtaTarjetastrasladofondoSuma +
            rtaCargosnodesados
        )

        print(
            f"""
            rtaRecepcionPago: {rtaRecepcionPago}
            rtaDevoluciones: {rtaDevoluciones}
            rtaGastogenerales: {rtaGastogenerales}
            rtaUtilidadocacional: {rtaUtilidadocacional}
            rtaCargosnodesados: {rtaCargosnodesados}
            total_general: {total_general}
            """
        )

        serializer.data[i]['valor'] = total_general

    return Response(serializer.data, status=status.HTTP_200_OK)

"""
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1,2)
def obtener_tarjetas_total(request):
    # Verificar si todas las tablas existen antes de ejecutar consultas
    required_models = {
        "RegistroTarjetas" : RegistroTarjetas,
        "RecepcionPago"    : RecepcionPago,
        "Devoluciones"     : Devoluciones,
        "Gastogenerales"   : Gastogenerales,
        "Utilidadocacional": Utilidadocacional,
        "Tarjetastrasladofondo":Tarjetastrasladofondo,
        "Cargosnodesados"  : Cargosnodesados
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

        rtaTarjetastrasladofondoResta = Tarjetastrasladofondo.objects.filter(
            id_tarjeta_bancaria_envia=serializer.data[i]['id']
        ).aggregate(
            total_suma=Sum(
                Cast(Replace(F('valor'), Value('.'), Value('')), output_field=models.IntegerField())
            )
        )

        rtaTarjetastrasladofondoSuma = Tarjetastrasladofondo.objects.filter(
            id_tarjeta_bancaria_recibe=serializer.data[i]['id']
        ).aggregate(
            total_suma=Sum(
                Cast(Replace(F('valor'), Value('.'), Value('')), output_field=models.IntegerField())
            )
        )



        rtaCuentaBancaria['total_suma']      = rtaCuentaBancaria['total_suma']     if rtaCuentaBancaria['total_suma']      is not None else 0
        rtaRecepcionPago['total_suma']       = rtaRecepcionPago['total_suma']      if rtaRecepcionPago['total_suma']       is not None else 0
        rtaDevoluciones['total_suma']        = rtaDevoluciones['total_suma']       if rtaDevoluciones['total_suma']        is not None else 0
        rtaGastogenerales['total_suma']      = rtaGastogenerales['total_suma']     if rtaGastogenerales['total_suma']      is not None else 0
        rtaUtilidadocacional['total_suma']   = rtaUtilidadocacional['total_suma']  if rtaUtilidadocacional['total_suma']   is not None else 0

        rtaTarjetastrasladofondoResta['total_suma']  = rtaTarjetastrasladofondoResta['total_suma']  if rtaTarjetastrasladofondoResta['total_suma']   is not None else 0
        rtaTarjetastrasladofondoSuma['total_suma']   = rtaTarjetastrasladofondoSuma['total_suma']  if rtaTarjetastrasladofondoSuma['total_suma']   is not None else 0

        total_general = (
            rtaCuentaBancaria['total_suma'] +
            rtaRecepcionPago['total_suma'] +
            rtaDevoluciones['total_suma'] +
            rtaGastogenerales['total_suma'] +
            rtaUtilidadocacional['total_suma'] -
            rtaTarjetastrasladofondoResta['total_suma'] +
            rtaTarjetastrasladofondoSuma['total_suma']
        )
        
        print("rtaRecepcionPago : {}\nrtaDevoluciones: {}\nrtaGastogenerales: {}\nrtaUtilidadocacional: {}\ntotal_general: {}"
            .format(rtaRecepcionPago, rtaDevoluciones, rtaGastogenerales, rtaUtilidadocacional, total_general))
    
        serializer.data[i]['valor'] = total_general

    return Response(serializer.data, status=status.HTTP_200_OK)
"""


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@check_role(1, 2)
def transferir_tarjeta(request, id, idtrans):
    try:
        nueva_tarjeta = RegistroTarjetas.objects.get(id=id)  
    except RegistroTarjetas.DoesNotExist:
        return Response({"error": "La tarjeta de destino no existe"}, status=status.HTTP_404_NOT_FOUND)

    try:
        tarjeta_antigua = RegistroTarjetas.objects.get(id=idtrans)
    except RegistroTarjetas.DoesNotExist:
        return Response({"error": "La tarjeta original no existe"}, status=status.HTTP_404_NOT_FOUND)

    try:
        with transaction.atomic():
            updated_cuentaBancaria = CuentaBancaria.objects.filter(idBanco=nueva_tarjeta.id).update(idBanco=tarjeta_antigua.id)
            updated_cotizador      = Cotizador.objects.filter(idBanco=nueva_tarjeta.id).update(idBanco=tarjeta_antigua.id)
            updated_recepcion      = RecepcionPago.objects.filter(id_tarjeta_bancaria=nueva_tarjeta).update(id_tarjeta_bancaria=tarjeta_antigua)
            updated_devoluciones   = Devoluciones.objects.filter(id_tarjeta_bancaria=nueva_tarjeta).update(id_tarjeta_bancaria=tarjeta_antigua)
            updated_gastos         = Gastogenerales.objects.filter(id_tarjeta_bancaria=nueva_tarjeta).update(id_tarjeta_bancaria=tarjeta_antigua)
            updated_utilidades     = Utilidadocacional.objects.filter(id_tarjeta_bancaria=nueva_tarjeta).update(id_tarjeta_bancaria=tarjeta_antigua)

            total_actualizados = updated_recepcion + updated_devoluciones + updated_gastos + updated_utilidades + updated_cotizador + updated_cuentaBancaria

            if total_actualizados == 0:
                return Response({"mensaje": "No se encontraron registros para actualizar."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            "mensaje": "Referencias actualizadas correctamente.",
            "detalles": {
                "updated_cotizador"     : updated_cotizador,
                "updated_cuentaBancaria": updated_cuentaBancaria,
                "recepcion_pago"        : updated_recepcion,
                "devoluciones"          : updated_devoluciones,
                "gastos_generales"      : updated_gastos,
                "utilidad_ocacional"    : updated_utilidades
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)