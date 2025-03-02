from django.shortcuts import render
import pandas as pd
# cuentas_bancarias/api/views.py
from django.utils.dateparse import parse_date
from datetime import datetime

from rest_framework.response    import Response
from django.http                import HttpResponse
from rest_framework.decorators  import api_view
from rest_framework             import status
from cuentasbancarias.models    import CuentaBancaria

from registroTarjetas.models    import RegistroTarjetas
from recepcionPago.models       import RecepcionPago
from devoluciones.models        import Devoluciones
from cotizador.models           import Cotizador
from gastosgenerales.models     import Gastogenerales
from utilidadocacional.models   import Utilidadocacional


from .serializers               import CuentaBancariaSerializer

from django.db.models import F, Value, CharField, Sum
from decimal import Decimal


@api_view(['GET'])
def obtener_cuentas(request):
    # Normalización de fechas y nombres de columnas sin sobrescribir nombres existentes
    cuentas = CuentaBancaria.objects.all().annotate(
        fi=F('fechaIngreso'),
        ft=F('fechaTransaccion'),
        desc_alias=F('descripcion'),  # Se usa 'desc_alias' en vez de 'descripcion'
        valor_alias=F('valor'),  # Se usa 'valor_alias' en vez de 'valor'
        id_tarjeta=F('idBanco')
    ).values('id', 'fi', 'ft', 'valor_alias', 'desc_alias','id_tarjeta')
    
    recepcionDePagos = RecepcionPago.objects.all().annotate(
        fi=F('fecha_ingreso'),
        ft=F('fecha_transaccion'),
        desc_alias=F('observacion'),
        valor_alias=F('valor'),
        id_tarjeta=F('id_tarjeta_bancaria')
    ).values('id', 'fi', 'ft', 'valor_alias', 'desc_alias','id_tarjeta')

    devoluciones = Devoluciones.objects.all().annotate(
        fi=F('fecha_ingreso'),
        ft=F('fecha_transaccion'),
        desc_alias=F('observacion'),
        valor_alias=F('valor'),
        id_tarjeta=F('id_tarjeta_bancaria')
    ).values('id', 'fi', 'ft', 'valor_alias', 'desc_alias', 'id_tarjeta')

    gastos = Gastogenerales.objects.all().annotate(
        fi=F('fecha_ingreso'),
        ft=F('fecha_transaccion'),
        desc_alias=F('observacion'),
        valor_alias=F('valor'),
        id_tarjeta=F('id_tarjeta_bancaria')
    ).values('id', 'fi', 'ft', 'valor_alias', 'desc_alias', 'id_tarjeta')

    utilidadocacional = Utilidadocacional.objects.all().annotate(
        fi=F('fecha_ingreso'),
        ft=F('fecha_transaccion'),
        desc_alias=F('observacion'),
        valor_alias=F('valor'),
        id_tarjeta=F('id_tarjeta_bancaria')
    ).values('id', 'fi', 'ft', 'valor_alias', 'desc_alias', 'id_tarjeta')

    # Unir todas las consultas asegurando que los tipos coincidan
    union_result = cuentas.union(devoluciones, gastos, utilidadocacional, recepcionDePagos)
   
    # Serializar el resultado; en el serializer, podrías convertir 'fi' y 'ft' a los nombres deseados

    return Response(union_result)

@api_view(['GET'])
def obtener_cuenta(request, id):
    try:
        cuenta      = CuentaBancaria.objects.get(id=id)
        cotizador   = Cotizador.objects.filter(id=cuenta.idCotizador).first()
        serializer  = CuentaBancariaSerializer(cuenta)

        # Agregar la URL del archivo al JSON de respuesta
        response_data = serializer.data
        # Obtener la URL del archivo si existe
        archivo_url = request.build_absolute_uri(cotizador.archivo.url) if cotizador.archivo else None

        # Agregar la URL del archivo a la respuesta JSON
        response_data["archivo"] = archivo_url

        return Response(response_data, status=status.HTTP_200_OK)
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


@api_view(['GET'])
def obtener_datos_cuenta(request, id):
    try:
        tarjeta = RegistroTarjetas.objects.get(pk=id)
        nombre_cuenta   = tarjeta.nombre_cuenta
        descripcion     = tarjeta.descripcion
        numero_cuenta   = tarjeta.numero_cuenta
        banco           = tarjeta.banco
    except:
        return Response({"error": "Tarjeta no encontrada"}, status=status.HTTP_404_NOT_FOUND)
    
    # Consulta para Cuentas Bancarias
    cuentas = CuentaBancaria.objects.filter(idBanco=id).annotate(
        fi=F('fechaIngreso'),
        ft=F('fechaTransaccion'),
        desc_alias=F('descripcion'),
        valor_alias=F('valor'),
        id_tarjeta=F('idBanco'),
        origen=Value('Cuenta Bancaria', output_field=CharField())
    ).values('id', 'fi', 'ft', 'valor_alias', 'desc_alias', 'id_tarjeta', 'origen')

    recepcionDePagos = RecepcionPago.objects.filter(id_tarjeta_bancaria=id).annotate(
        fi=F('fecha_ingreso'),
        ft=F('fecha_transaccion'),
        desc_alias=F('observacion'),
        valor_alias=F('valor'),
        id_tarjeta=F('id_tarjeta_bancaria'),
        origen=Value('Recepcion de Pago', output_field=CharField())
    ).values('id', 'fi', 'ft', 'valor_alias', 'desc_alias', 'id_tarjeta', 'origen')

    # Consulta para Devoluciones
    devoluciones = Devoluciones.objects.filter(id_tarjeta_bancaria=id).annotate(
        fi=F('fecha_ingreso'),
        ft=F('fecha_transaccion'),
        desc_alias=F('observacion'),
        valor_alias=F('valor'),
        id_tarjeta=F('id_tarjeta_bancaria'),
        origen=Value('Devolución', output_field=CharField())
    ).values('id', 'fi', 'ft', 'valor_alias', 'desc_alias', 'id_tarjeta', 'origen')

    # Consulta para Gastos Generales
    gastos = Gastogenerales.objects.filter(id_tarjeta_bancaria=id).annotate(
        fi=F('fecha_ingreso'),
        ft=F('fecha_transaccion'),
        desc_alias=F('observacion'),
        valor_alias=F('valor'),
        id_tarjeta=F('id_tarjeta_bancaria'),
        origen=Value('Gasto General', output_field=CharField())
    ).values('id', 'fi', 'ft', 'valor_alias', 'desc_alias', 'id_tarjeta', 'origen')

    # Consulta para Utilidad Ocasional
    utilidadocacional = Utilidadocacional.objects.filter(id_tarjeta_bancaria=id).annotate(
        fi=F('fecha_ingreso'),
        ft=F('fecha_transaccion'),
        desc_alias=F('observacion'),
        valor_alias=F('valor'),
        id_tarjeta=F('id_tarjeta_bancaria'),
        origen=Value('Utilidad Ocasional', output_field=CharField())
    ).values('id', 'fi', 'ft', 'valor_alias', 'desc_alias', 'id_tarjeta', 'origen')

    # Unir todas las consultas asegurando que los tipos coincidan
    union_result = list(cuentas.union(devoluciones, gastos, utilidadocacional, recepcionDePagos))

    # Calcular totales de cada categoría
    total_cuentas           = safe_sum(CuentaBancaria.objects.filter(idBanco=id), "valor")
    total_devoluciones      = safe_sum(Devoluciones.objects.filter(id_tarjeta_bancaria=id), "valor")
    total_gastos            = safe_sum(Gastogenerales.objects.filter(id_tarjeta_bancaria=id), "valor")
    total_utilidad          = safe_sum(Utilidadocacional.objects.filter(id_tarjeta_bancaria=id), "valor")
    total_recepcionDePagos  = safe_sum(RecepcionPago.objects.filter(id_tarjeta_bancaria=id), "valor")

    # Calcular el total de todas las categorías
    total_general = total_cuentas + total_devoluciones + total_gastos + total_utilidad + total_recepcionDePagos

    # Objeto con los totales
    response_data = {
        "data": list(union_result),  # Convierte el QuerySet en lista
        "totales": {
            "total_cuenta_bancaria"     : total_cuentas or 0,
            "total_devoluciones"        : total_devoluciones or 0,
            "total_gastos_generales"    : total_gastos or 0,
            "total_utilidad_ocacional"  : total_utilidad or 0,
            "total_recepcionDePagos"    : total_recepcionDePagos or 0,
            "total"                     : total_general or 0
        },
        "tarjeta":{
            "nombre_cuenta"     : nombre_cuenta,
            "descripcion_cuenta": descripcion,
            "numero_cuenta"     : numero_cuenta,
            "banco"             : banco,
        }
    }

    # Respuesta JSON combinando los datos y los totales
    return Response(response_data, status=status.HTTP_200_OK)

@api_view(['GET'])
def cuentasbancarias_filter_date(request, id):
    # Obtener los parámetros de fecha de la URL

    fecha_inicio = request.GET.get('fechaInicio')
    fecha_fin = request.GET.get('fechaFin')


    # Convertir las fechas a objetos de Python
    fecha_inicio = parse_date_with_defaults(fecha_inicio)
    fecha_fin = parse_date_with_defaults(fecha_fin, is_end=True)


    print("fecha_inicio {}".format(fecha_inicio))
    print("fecha_fin {}".format(fecha_fin))
    try:
        tarjeta = RegistroTarjetas.objects.get(pk=id)
        nombre_cuenta   = tarjeta.nombre_cuenta
        descripcion     = tarjeta.descripcion
        numero_cuenta   = tarjeta.numero_cuenta
        banco           = tarjeta.banco
    except RegistroTarjetas.DoesNotExist:
        return Response({"error": "Tarjeta no encontrada"}, status=status.HTTP_404_NOT_FOUND)

    # Función auxiliar para filtrar por fecha
    def filter_by_date(queryset, field_name):
        if fecha_inicio and fecha_fin:
            return queryset.filter(**{f"{field_name}__range": [fecha_inicio, fecha_fin]})
        elif fecha_inicio:
            return queryset.filter(**{f"{field_name}__gte": fecha_inicio})
        elif fecha_fin:
            return queryset.filter(**{f"{field_name}__lte": fecha_fin})
        return queryset

    # Filtrar y agregar alias en cada consulta
    cuentas = filter_by_date(CuentaBancaria.objects.filter(idBanco=id), "fechaIngreso").annotate(
        fi=F('fechaIngreso'),
        ft=F('fechaTransaccion'),
        desc_alias=F('descripcion'),
        valor_alias=F('valor'),
        id_tarjeta=F('idBanco'),
        origen=Value('Cuenta Bancaria', output_field=CharField())
    ).values('id', 'fi', 'ft', 'valor_alias', 'desc_alias', 'id_tarjeta', 'origen')

    recepcionDePagos = filter_by_date(RecepcionPago.objects.filter(id_tarjeta_bancaria=id), "fecha_ingreso").annotate(
        fi=F('fecha_ingreso'),
        ft=F('fecha_transaccion'),
        desc_alias=F('observacion'),
        valor_alias=F('valor'),
        id_tarjeta=F('id_tarjeta_bancaria'),
        origen=Value('Recepcion de Pago', output_field=CharField())
    ).values('id', 'fi', 'ft', 'valor_alias', 'desc_alias', 'id_tarjeta', 'origen')

    devoluciones = filter_by_date(Devoluciones.objects.filter(id_tarjeta_bancaria=id), "fecha_ingreso").annotate(
        fi=F('fecha_ingreso'),
        ft=F('fecha_transaccion'),
        desc_alias=F('observacion'),
        valor_alias=F('valor'),
        id_tarjeta=F('id_tarjeta_bancaria'),
        origen=Value('Devolución', output_field=CharField())
    ).values('id', 'fi', 'ft', 'valor_alias', 'desc_alias', 'id_tarjeta', 'origen')

    gastos = filter_by_date(Gastogenerales.objects.filter(id_tarjeta_bancaria=id), "fecha_ingreso").annotate(
        fi=F('fecha_ingreso'),
        ft=F('fecha_transaccion'),
        desc_alias=F('observacion'),
        valor_alias=F('valor'),
        id_tarjeta=F('id_tarjeta_bancaria'),
        origen=Value('Gasto General', output_field=CharField())
    ).values('id', 'fi', 'ft', 'valor_alias', 'desc_alias', 'id_tarjeta', 'origen')

    utilidadocacional = filter_by_date(Utilidadocacional.objects.filter(id_tarjeta_bancaria=id), "fecha_ingreso").annotate(
        fi=F('fecha_ingreso'),
        ft=F('fecha_transaccion'),
        desc_alias=F('observacion'),
        valor_alias=F('valor'),
        id_tarjeta=F('id_tarjeta_bancaria'),
        origen=Value('Utilidad Ocasional', output_field=CharField())
    ).values('id', 'fi', 'ft', 'valor_alias', 'desc_alias', 'id_tarjeta', 'origen')

    # Unir todas las consultas asegurando que los tipos coincidan
    union_result = list(cuentas.union(devoluciones, gastos, utilidadocacional, recepcionDePagos))

    total_cuentas = safe_sum(filter_by_date(CuentaBancaria.objects.filter(idBanco=id), "fechaIngreso"), "valor")
    total_devoluciones = safe_sum(filter_by_date(Devoluciones.objects.filter(id_tarjeta_bancaria=id), "fecha_ingreso"), "valor")
    total_gastos = safe_sum(filter_by_date(Gastogenerales.objects.filter(id_tarjeta_bancaria=id), "fecha_ingreso"), "valor")
    total_utilidad = safe_sum(filter_by_date(Utilidadocacional.objects.filter(id_tarjeta_bancaria=id), "fecha_ingreso"), "valor")
    total_recepcionDePagos = safe_sum(filter_by_date(RecepcionPago.objects.filter(id_tarjeta_bancaria=id), "fecha_ingreso"), "valor")

    # Calcular el total de todas las categorías
    total_general = total_cuentas + total_devoluciones + total_gastos + total_utilidad + total_recepcionDePagos

    # Objeto con los totales
    response_data = {
        "data": list(union_result),  # Convierte el QuerySet en lista
        "totales": {
            "total_cuenta_bancaria": total_cuentas or 0,
            "total_devoluciones": total_devoluciones or 0,
            "total_gastos_generales": total_gastos or 0,
            "total_utilidad_ocacional": total_utilidad or 0,
            "total_recepcionDePagos": total_recepcionDePagos or 0,
            "total": total_general or 0
        },
        "tarjeta": {
            "nombre_cuenta": nombre_cuenta,
            "descripcion_cuenta": descripcion,
            "numero_cuenta": numero_cuenta,
            "banco": banco,
        }
    }

    # Respuesta JSON combinando los datos y los totales
    return Response(response_data, status=status.HTTP_200_OK)


def parse_date_with_defaults(date_str, is_end=False):
    if not date_str:
        return None
    
    parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
    if is_end:
        parsed_date = parsed_date.replace(hour=23, minute=59, second=59)
    else:
        parsed_date = parsed_date.replace(hour=0, minute=0, second=0)
    
    return parsed_date

def safe_sum(queryset, field_name):
    """
    Recupera valores de un queryset y los convierte a Decimal para sumarlos.
    Si un valor no puede convertirse, se ignora.
    """
    valores = queryset.values_list(field_name, flat=True)
    total = Decimal(0)

    for valor in valores:
        try:
            # Limpiar separadores de miles y convertir a Decimal
            valor_str = str(valor).replace(".", "")  # Elimina separador de miles
            valor_str = valor_str.replace(",", ".")  # Convierte coma decimal a punto
            
            valor_decimal = Decimal(valor_str)  # Convierte a Decimal
            total += valor_decimal  # Suma respetando valores negativos
        except (ValueError, TypeError):
            print(f"Advertencia: No se pudo convertir el valor '{valor}' en la base de datos.")
            continue  # Ignorar valores inválidos

    return total


@api_view(["GET"])
def download_report_excel(request, id):
    try:
        print(f"ID recibido: {id}")  # Depuración

        if not str(id).isdigit():
            return Response({"error": "ID inválido"}, status=status.HTTP_400_BAD_REQUEST)

        tarjeta = RegistroTarjetas.objects.get(pk=id)

        cuentas = CuentaBancaria.objects.filter(idBanco=id)
        recepcionDePagos = RecepcionPago.objects.filter(id_tarjeta_bancaria=id)
        devoluciones = Devoluciones.objects.filter(id_tarjeta_bancaria=id)
        gastos = Gastogenerales.objects.filter(id_tarjeta_bancaria=id)
        utilidadocacional = Utilidadocacional.objects.filter(id_tarjeta_bancaria=id)

        # Depuración
        print(f"Cuentas encontradas: {cuentas.count()}")
        print(f"Recepcion de Pagos encontradas: {recepcionDePagos.count()}")
        print(f"Devoluciones encontradas: {devoluciones.count()}")
        print(f"Gastos encontrados: {gastos.count()}")
        print(f"Utilidades ocasionales encontradas: {utilidadocacional.count()}")

    except RegistroTarjetas.DoesNotExist:
        return Response({"error": "Tarjeta no encontrada"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"Error inesperado: {e}")  # Depuración en logs
        return Response({"error": "Error interno en el servidor"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
def download_report_pdf(request, id):
    pass