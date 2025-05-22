from django.shortcuts import render
import pandas as pd
# cuentas_bancarias/api/views.py
from django.utils.dateparse import parse_date
from datetime import datetime

from rest_framework.response    import Response
from django.http                import HttpResponse
from rest_framework.decorators  import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework             import status
from cuentasbancarias.models    import CuentaBancaria

from registroTarjetas.models    import RegistroTarjetas
from recepcionPago.models       import RecepcionPago
from devoluciones.models        import Devoluciones
from cotizador.models           import Cotizador
from gastosgenerales.models     import Gastogenerales
from utilidadocacional.models   import Utilidadocacional


from .serializers               import CuentaBancariaSerializer

from django.db.models import F, Value, CharField, Sum, IntegerField, Q
from decimal import Decimal

from tempfile import NamedTemporaryFile
from users.decorators import check_role

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1,2)
def obtener_cuentas(request):
    # Obtener todas las cuentas bancarias con los campos necesarios sergio 
    cuentas_qs = CuentaBancaria.objects.annotate(
        fi=F('fechaIngreso'),
        ft=F('fechaTransaccion'),
        desc_alias=F('descripcion'),
        valor_alias=F('valor'),
        id_tarjeta=F('idBanco'),
        origen=Value("Tramite", output_field=CharField()),
        id_cotizador=F('idCotizador')
    ).values('id', 'fi', 'ft', 'valor_alias','cuatro_por_mil', 'desc_alias', 'id_tarjeta', 'origen', 'id_cotizador')

    # Obtener todos los cotizadores en un diccionario {id: objeto}
    cotizador_ids = [c['id_cotizador'] for c in cuentas_qs if c['id_cotizador']]
    cotizadores = {c.id: c for c in Cotizador.objects.filter(id__in=cotizador_ids)}

    # Convertir cuentas a lista y agregar datos de Cotizador
    cuentas = list(cuentas_qs)
    for cuenta in cuentas:
        cotizador = cotizadores.get(cuenta.get('id_cotizador'))
        cuenta['placa'] = cotizador.placa if cotizador else None
        cuenta['cilindraje'] = cotizador.cilindraje if cotizador else None
        cuenta['archivo'] = cotizador.archivo.url if cotizador and cotizador.archivo else None

    # Obtener datos de las otras tablas y convertirlas en listas
    recepcionDePagos = list(RecepcionPago.objects.annotate(
        fi=F('fecha_ingreso'),
        ft=F('fecha_transaccion'),
        desc_alias=F('observacion'),
        valor_alias=F('valor'),
        id_tarjeta=F('id_tarjeta_bancaria'),
        origen=Value("Recepcion Pago", output_field=CharField()),
        id_cotizador=Value(None, output_field=IntegerField()),
    ).values('id', 'fi', 'ft', 'valor_alias','cuatro_por_mil', 'desc_alias', 'id_tarjeta', 'origen', 'id_cotizador'))

    devoluciones = list(Devoluciones.objects.annotate(
        fi=F('fecha_ingreso'),
        ft=F('fecha_transaccion'),
        desc_alias=F('observacion'),
        valor_alias=F('valor'),
        id_tarjeta=F('id_tarjeta_bancaria'),
        origen=Value("Devoluciones", output_field=CharField()),
        id_cotizador=Value(None, output_field=IntegerField()),
    ).values('id', 'fi', 'ft', 'valor_alias','cuatro_por_mil', 'desc_alias', 'id_tarjeta', 'origen', 'id_cotizador'))

    gastos = list(Gastogenerales.objects.annotate(
        fi=F('fecha_ingreso'),
        ft=F('fecha_transaccion'),
        desc_alias=F('observacion'),
        valor_alias=F('valor'),
        id_tarjeta=F('id_tarjeta_bancaria'),
        origen=Value("Gastos generales", output_field=CharField()),
        id_cotizador=Value(None, output_field=IntegerField()),
    ).values('id', 'fi', 'ft', 'valor_alias','cuatro_por_mil', 'desc_alias', 'id_tarjeta', 'origen', 'id_cotizador'))

    utilidadocacional = list(Utilidadocacional.objects.annotate(
        fi=F('fecha_ingreso'),
        ft=F('fecha_transaccion'),
        desc_alias=F('observacion'),
        valor_alias=F('valor'),
        id_tarjeta=F('id_tarjeta_bancaria'),
        origen=Value("Utilidad ocacional", output_field=CharField()),
        id_cotizador=Value(None, output_field=IntegerField()),
    ).values('id', 'fi', 'ft', 'valor_alias','cuatro_por_mil', 'desc_alias', 'id_tarjeta', 'origen', 'id_cotizador'))

    # Unir los datos como listas
    union_result = cuentas + recepcionDePagos + devoluciones + gastos + utilidadocacional

    # Retornar la respuesta
    return Response(union_result)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1,2)
def obtener_cuentas_filtradas(request):
    # Obtener parámetros de fecha desde la URL
    fecha_inicio = parse_date_with_defaults(request.GET.get('fechaInicio'))
    fecha_fin = parse_date_with_defaults(request.GET.get('fechaFin'), is_end=True)

    # Aplicar filtro de fechas en `fi`
    filtro_fecha = Q()
    if fecha_inicio and fecha_fin:
        filtro_fecha = Q(fi__range=[fecha_inicio, fecha_fin])
    elif fecha_inicio:
        filtro_fecha = Q(fi__gte=fecha_inicio)
    elif fecha_fin:
        filtro_fecha = Q(fi__lte=fecha_fin)

    # Obtener todas las cuentas bancarias con filtro de fecha en `fi`
    cuentas_qs = CuentaBancaria.objects.annotate(
        fi=F('fechaIngreso'),
        ft=F('fechaTransaccion'),
        desc_alias=F('descripcion'),
        valor_alias=F('valor'),
        id_tarjeta=F('idBanco'),
        origen=Value("Tramite", output_field=CharField()),
        id_cotizador=F('idCotizador')
    ).filter(filtro_fecha).values('id', 'fi', 'ft', 'valor_alias', 'desc_alias', 'id_tarjeta', 'origen', 'id_cotizador')

    # Obtener cotizadores en un diccionario {id: objeto}
    cotizador_ids = [c['id_cotizador'] for c in cuentas_qs if c['id_cotizador']]
    cotizadores = {c.id: c for c in Cotizador.objects.filter(id__in=cotizador_ids)}

    # Convertir cuentas a lista y agregar datos de Cotizador
    cuentas = list(cuentas_qs)
    for cuenta in cuentas:
        cotizador = cotizadores.get(cuenta.get('id_cotizador'))
        cuenta['placa'] = cotizador.placa if cotizador else None
        cuenta['cilindraje'] = cotizador.cilindraje if cotizador else None
        cuenta['archivo'] = cotizador.archivo.url if cotizador and cotizador.archivo else None

    # Listado de tablas adicionales a procesar
    otras_tablas = [
        (RecepcionPago, "Recepcion Pago"),
        (Devoluciones, "Devoluciones"),
        (Gastogenerales, "Gastos generales"),
        (Utilidadocacional, "Utilidad ocacional")
    ]

    # Unir resultados de todas las consultas
    union_result = cuentas

    for tabla, origen in otras_tablas:
        registros = list(tabla.objects.annotate(
            fi=F('fecha_ingreso'),
            ft=F('fecha_transaccion'),
            desc_alias=F('observacion'),
            valor_alias=F('valor'),
            id_tarjeta=F('id_tarjeta_bancaria'),
            origen=Value(origen, output_field=CharField()),
            id_cotizador=Value(None, output_field=IntegerField()),
        ).filter(filtro_fecha).values('id', 'fi', 'ft', 'valor_alias', 'desc_alias', 'id_tarjeta', 'origen', 'id_cotizador'))
        union_result.extend(registros)

    # Retornar la respuesta
    return Response(union_result)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1,2)
def obtener_cuenta(request, id):
    try:
        # Obtener la cuenta bancaria
        cuenta    = CuentaBancaria.objects.get(id=id)
        cotizador = Cotizador.objects.filter(id=cuenta.idCotizador).first()

        # Construir manualmente el diccionario de respuesta
        response_data = {
            "id": cuenta.id,
            "fecha_ingreso": cuenta.fechaIngreso,
            "fecha_transaccion": cuenta.fechaTransaccion,
            "descripcion": cuenta.descripcion,
            "valor": cuenta.valor,
            "id_banco": cuenta.idBanco,
            "origen": "Tramite",
            "id_cotizador": cuenta.idCotizador,
            "placa": cotizador.placa if cotizador else None,
            "cilindraje": cotizador.cilindraje if cotizador else None,
            "archivo": request.build_absolute_uri(cotizador.archivo.url) if cotizador and cotizador.archivo else None
        }

        return Response(response_data, status=status.HTTP_200_OK)
    
    except CuentaBancaria.DoesNotExist:
        return Response({"error": "Cuenta bancaria no encontrada"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@check_role(1,2)
def crear_cuenta(request):
    serializer = CuentaBancariaSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@check_role(1,2)
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
@permission_classes([IsAuthenticated])
@check_role(1,2)
def eliminar_cuenta(request, id):
    try:
        cuenta = CuentaBancaria.objects.get(id=id)
        cuenta.delete()
        return Response({"message": "Cuenta bancaria eliminada correctamente"}, status=status.HTTP_204_NO_CONTENT)
    except CuentaBancaria.DoesNotExist:
        return Response({"error": "Cuenta bancaria no encontrada"}, status=status.HTTP_404_NOT_FOUND)

def ordenar_union_result(union_result):
    """
    Ordena la lista union_result por la fecha de ingreso (fi) en orden descendente.
    """
    transacciones_ordenadas = sorted(union_result, key=lambda x: x['fi'], reverse=True)
    return transacciones_ordenadas

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1,2)
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
        origen=Value('Cuenta Bancaria', output_field=CharField()),
        id_cotizador=F('idCotizador'),
        placa=Value(None, output_field=IntegerField()),
    ).values('id', 'fi', 'ft', 'valor_alias', 'cuatro_por_mil','desc_alias', 'id_tarjeta', 'origen', 'id_cotizador','placa')

    
    cotizador_ids = [c['id_cotizador'] for c in cuentas if c['id_cotizador']]
    cotizadores = {c.id: c for c in Cotizador.objects.filter(id__in=cotizador_ids)}
 
    for cuenta in cuentas:
        cotizador = cotizadores.get(cuenta.get('id_cotizador'))
        if cotizador:
            cuenta['placa'] = cotizador.placa
        else:
            cuenta['placa'] = None

    print(" ========= cuentas ======== ",cuentas)
    recepcionDePagos = RecepcionPago.objects.filter(id_tarjeta_bancaria=id).annotate(
        fi=F('fecha_ingreso'),
        ft=F('fecha_transaccion'),
        desc_alias=F('observacion'),
        valor_alias=F('valor'),
        id_tarjeta=F('id_tarjeta_bancaria'),
        origen=Value('Recepcion de Pago', output_field=CharField()),
        id_cotizador=Value(None, output_field=IntegerField()),
        placa=Value(None, output_field=IntegerField()),
    ).values('id', 'fi', 'ft', 'valor_alias','cuatro_por_mil', 'desc_alias', 'id_tarjeta', 'origen', 'id_cotizador', 'placa')

    # Consulta para Devoluciones
    devoluciones = Devoluciones.objects.filter(id_tarjeta_bancaria=id).annotate(
        fi=F('fecha_ingreso'),
        ft=F('fecha_transaccion'),
        desc_alias=F('observacion'),
        valor_alias=F('valor'),
        id_tarjeta=F('id_tarjeta_bancaria'),
        origen=Value('Devolución', output_field=CharField()),
        id_cotizador=Value(None, output_field=IntegerField()),
        placa=Value(None, output_field=IntegerField()),
    ).values('id', 'fi', 'ft', 'valor_alias','cuatro_por_mil', 'desc_alias', 'id_tarjeta', 'origen', 'id_cotizador', 'placa')

    # Consulta para Gastos Generales
    gastos = Gastogenerales.objects.filter(id_tarjeta_bancaria=id).annotate(
        fi=F('fecha_ingreso'),
        ft=F('fecha_transaccion'),
        desc_alias=F('observacion'),
        valor_alias=F('valor'),
        id_tarjeta=F('id_tarjeta_bancaria'),
        origen=Value('Gasto General', output_field=CharField()),
        id_cotizador=Value(None, output_field=IntegerField()),
        placa=Value(None, output_field=IntegerField()),
    ).values('id', 'fi', 'ft', 'valor_alias','cuatro_por_mil', 'desc_alias', 'id_tarjeta', 'origen', 'id_cotizador', 'placa')

    # Consulta para Utilidad Ocasional
    utilidadocacional = Utilidadocacional.objects.filter(id_tarjeta_bancaria=id).annotate(
        fi=F('fecha_ingreso'),
        ft=F('fecha_transaccion'),
        desc_alias=F('observacion'),
        valor_alias=F('valor'),
        id_tarjeta=F('id_tarjeta_bancaria'),
        origen=Value('Utilidad Ocasional', output_field=CharField()),
        id_cotizador=Value(None, output_field=IntegerField()),
        placa=Value(None, output_field=IntegerField()),
    ).values('id', 'fi', 'ft', 'valor_alias','cuatro_por_mil', 'desc_alias', 'id_tarjeta', 'origen', 'id_cotizador', 'placa')

    # Unir todas las consultas asegurando que los tipos coincidan

    union_result = list(cuentas) + list(devoluciones) + list(gastos) + list(utilidadocacional) + list(recepcionDePagos)
 
    # Calcular totales de cada categoría
    total_cuentas           = safe_sum(CuentaBancaria.objects.filter(idBanco=id), "valor")
    total_devoluciones      = safe_sum(Devoluciones.objects.filter(id_tarjeta_bancaria=id), "valor")
    total_gastos            = safe_sum(Gastogenerales.objects.filter(id_tarjeta_bancaria=id), "valor")
    total_utilidad          = safe_sum(Utilidadocacional.objects.filter(id_tarjeta_bancaria=id), "valor")
    total_recepcionDePagos  = safe_sum(RecepcionPago.objects.filter(id_tarjeta_bancaria=id), "valor")

    # Calcular el total de todas las categorías
    total_general = total_cuentas + total_devoluciones + total_gastos + total_utilidad + total_recepcionDePagos
    transacciones_ordenadas = ordenar_union_result(union_result)

    # Objeto con los totales
    response_data = {
        "data": list(transacciones_ordenadas),  # Convierte el QuerySet en lista
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
@permission_classes([IsAuthenticated])
@check_role(1,2)
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
    ).values('id', 'fi', 'ft', 'valor_alias','cuatro_por_mil', 'desc_alias', 'id_tarjeta', 'origen')

    recepcionDePagos = filter_by_date(RecepcionPago.objects.filter(id_tarjeta_bancaria=id), "fecha_ingreso").annotate(
        fi=F('fecha_ingreso'),
        ft=F('fecha_transaccion'),
        desc_alias=F('observacion'),
        valor_alias=F('valor'),
        id_tarjeta=F('id_tarjeta_bancaria'),
        origen=Value('Recepcion de Pago', output_field=CharField())
    ).values('id', 'fi', 'ft', 'valor_alias', 'cuatro_por_mil','desc_alias', 'id_tarjeta', 'origen')

    devoluciones = filter_by_date(Devoluciones.objects.filter(id_tarjeta_bancaria=id), "fecha_ingreso").annotate(
        fi=F('fecha_ingreso'),
        ft=F('fecha_transaccion'),
        desc_alias=F('observacion'),
        valor_alias=F('valor'),
        id_tarjeta=F('id_tarjeta_bancaria'),
        origen=Value('Devolución', output_field=CharField())
    ).values('id', 'fi', 'ft', 'valor_alias','cuatro_por_mil', 'desc_alias', 'id_tarjeta', 'origen')

    gastos = filter_by_date(Gastogenerales.objects.filter(id_tarjeta_bancaria=id), "fecha_ingreso").annotate(
        fi=F('fecha_ingreso'),
        ft=F('fecha_transaccion'),
        desc_alias=F('observacion'),
        valor_alias=F('valor'),
        id_tarjeta=F('id_tarjeta_bancaria'),
        origen=Value('Gasto General', output_field=CharField())
    ).values('id', 'fi', 'ft', 'valor_alias','cuatro_por_mil', 'desc_alias', 'id_tarjeta', 'origen')

    utilidadocacional = filter_by_date(Utilidadocacional.objects.filter(id_tarjeta_bancaria=id), "fecha_ingreso").annotate(
        fi=F('fecha_ingreso'),
        ft=F('fecha_transaccion'),
        desc_alias=F('observacion'),
        valor_alias=F('valor'),
        id_tarjeta=F('id_tarjeta_bancaria'),
        origen=Value('Utilidad Ocasional', output_field=CharField())
    ).values('id', 'fi', 'ft', 'valor_alias','cuatro_por_mil', 'desc_alias', 'id_tarjeta', 'origen')

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
@permission_classes([IsAuthenticated])
@check_role(1,2)
def download_report_excel(request, id):
    # Obtener los parámetros de fecha de la URL
    fecha_inicio = request.GET.get('fechaInicio')
    fecha_fin    = request.GET.get('fechaFin')


    # Convertir las fechas a objetos de Python
    fecha_inicio = parse_date_with_defaults(fecha_inicio)
    fecha_fin    = parse_date_with_defaults(fecha_fin, is_end=True)

    if fecha_fin and fecha_fin:
        print(" ===== Ingesa =====")
        try:
            # Validar que el ID es un número válido
            if not str(id).isdigit():
                return Response({"error": "ID inválido"}, status=status.HTTP_400_BAD_REQUEST)

            tarjeta = RegistroTarjetas.objects.filter(pk=id).first()
            if not tarjeta:
                return Response({"error": "Tarjeta no encontrada"}, status=status.HTTP_404_NOT_FOUND)

            # Extraer información de la tarjeta
            nombre_cuenta = tarjeta.nombre_cuenta
            descripcion = tarjeta.descripcion
            numero_cuenta = tarjeta.numero_cuenta
            banco = tarjeta.banco

            # Consultas optimizadas
            cuentas = CuentaBancaria.objects.filter(idBanco=id).annotate(
                fi=F("fechaIngreso"),
                ft=F("fechaTransaccion"),
                desc_alias=F("descripcion"),
                valor_alias=F("valor"),
                id_tarjeta=F("idBanco"),
                origen=Value("Cuenta Bancaria", output_field=CharField())
            ).values("id", "fi", "ft", "valor_alias", "desc_alias", "id_tarjeta", "origen")
            cuentas = cuentas.filter(fi__range=(fecha_inicio, fecha_fin))

            recepcionDePagos = RecepcionPago.objects.filter(id_tarjeta_bancaria=id).annotate(
                fi=F('fecha_ingreso'),
                ft=F('fecha_transaccion'),
                desc_alias=F('observacion'),
                valor_alias=F('valor'),
                id_tarjeta=F('id_tarjeta_bancaria'),
                origen=Value('Recepcion de Pago', output_field=CharField())
            ).values('id', 'fi', 'ft', 'valor_alias', 'desc_alias', 'id_tarjeta', 'origen')
            recepcionDePagos = recepcionDePagos.filter(fi__range=(fecha_inicio, fecha_fin))

            devoluciones = Devoluciones.objects.filter(id_tarjeta_bancaria=id).annotate(
                fi=F("fecha_ingreso"),
                ft=F("fecha_transaccion"),
                desc_alias=F("observacion"),
                valor_alias=F("valor"),
                id_tarjeta=F("id_tarjeta_bancaria"),
                origen=Value("Devolución", output_field=CharField())
            ).values("id", "fi", "ft", "valor_alias", "desc_alias", "id_tarjeta", "origen")
            devoluciones = devoluciones.filter(fi__range=(fecha_inicio, fecha_fin))

            gastos = Gastogenerales.objects.filter(id_tarjeta_bancaria=id).annotate(
                fi=F("fecha_ingreso"),
                ft=F("fecha_transaccion"),
                desc_alias=F("observacion"),
                valor_alias=F("valor"),
                id_tarjeta=F("id_tarjeta_bancaria"),
                origen=Value("Gasto General", output_field=CharField())
            ).values("id", "fi", "ft", "valor_alias", "desc_alias", "id_tarjeta", "origen")
            gastos = gastos.filter(fi__range=(fecha_inicio, fecha_fin))
            
            utilidadocacional = Utilidadocacional.objects.filter(id_tarjeta_bancaria=id).annotate(
                fi=F("fecha_ingreso"),
                ft=F("fecha_transaccion"),
                desc_alias=F("observacion"),
                valor_alias=F("valor"),
                id_tarjeta=F("id_tarjeta_bancaria"),
                origen=Value("Utilidad Ocasional", output_field=CharField())
            ).values("id", "fi", "ft", "valor_alias", "desc_alias", "id_tarjeta", "origen")
            utilidadocacional = utilidadocacional.filter(fi__range=(fecha_inicio, fecha_fin))

            # Unir todas las consultas
            union_result = list(cuentas) + list(recepcionDePagos) + list(devoluciones) + list(gastos) + list(utilidadocacional)

            # Crear DataFrame con los datos
            df = pd.DataFrame(union_result)

            # Renombrar columnas si hay datos
            if not df.empty:
                df.rename(columns={
                    "fi": "Fecha Ingreso",
                    "ft": "Fecha Transacción",
                    "desc_alias": "Descripción",
                    "valor_alias": "Valor",
                    "id_tarjeta": "ID Tarjeta",
                    "origen": "Tipo de Movimiento",
                }, inplace=True)

                # Formatear fechas si existen
                if "Fecha Ingreso" in df.columns:
                    df["Fecha Ingreso"] = pd.to_datetime(df["Fecha Ingreso"]).dt.tz_localize(None)
                if "Fecha Transacción" in df.columns:
                    df["Fecha Transacción"] = pd.to_datetime(df["Fecha Transacción"]).dt.tz_localize(None)

            # Calcular totales
            total_cuentas           = safe_sum( CuentaBancaria.objects.filter(idBanco=id).filter(fechaIngreso__range=(fecha_inicio, fecha_fin)), "valor")
            total_devoluciones      = safe_sum(Devoluciones.objects.filter(id_tarjeta_bancaria=id).filter(fecha_ingreso__range=(fecha_inicio, fecha_fin)), "valor")
            total_gastos            = safe_sum(Gastogenerales.objects.filter(id_tarjeta_bancaria=id).filter(fecha_ingreso__range=(fecha_inicio, fecha_fin)), "valor")
            total_utilidad          = safe_sum(Utilidadocacional.objects.filter(id_tarjeta_bancaria=id).filter(fecha_ingreso__range=(fecha_inicio, fecha_fin)), "valor")
            total_recepcionDePagos  = safe_sum(RecepcionPago.objects.filter(id_tarjeta_bancaria=id).filter(fecha_ingreso__range=(fecha_inicio, fecha_fin)), "valor")

            total_general = total_cuentas + total_devoluciones + total_gastos + total_utilidad + total_recepcionDePagos

            # Crear DataFrame con los totales
            df_totales = pd.DataFrame({
                "Concepto": ["Total Cuenta Bancaria", "Total Devoluciones", "Total Gastos Generales", "Total Utilidad Ocasional", "Total Recepcion de pagos", "TOTAL GENERAL"],
                "Valor": [total_cuentas, total_devoluciones, total_gastos, total_utilidad, total_recepcionDePagos, total_general]
            })

            # Crear DataFrame con la información de la tarjeta
            df_tarjeta = pd.DataFrame({
                "Campo": ["Nombre Cuenta", "Descripción", "Número Cuenta", "Banco"],
                "Valor": [nombre_cuenta, descripcion, numero_cuenta, banco]
            })

            # Usar un archivo temporal para evitar problemas de concurrencia
            with NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                with pd.ExcelWriter(tmp.name, engine="xlsxwriter") as writer:
                    df_tarjeta.to_excel(writer, sheet_name="Información Cuenta", index=False)
                    df.to_excel(writer, sheet_name="Movimientos", index=False)
                    df_totales.to_excel(writer, sheet_name="Totales", index=False)

                # Leer el archivo Excel y enviarlo como respuesta HTTP
                with open(tmp.name, "rb") as excel_file:
                    response = HttpResponse(excel_file.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    response["Content-Disposition"] = f'attachment; filename="Reporte_Cuenta_{id}.xlsx"'
            return response
        except Exception as e:
            return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    try:
        # Validar que el ID es un número válido
        if not str(id).isdigit():
            return Response({"error": "ID inválido"}, status=status.HTTP_400_BAD_REQUEST)

        tarjeta = RegistroTarjetas.objects.filter(pk=id).first()
        if not tarjeta:
            return Response({"error": "Tarjeta no encontrada"}, status=status.HTTP_404_NOT_FOUND)

        # Extraer información de la tarjeta
        nombre_cuenta = tarjeta.nombre_cuenta
        descripcion = tarjeta.descripcion
        numero_cuenta = tarjeta.numero_cuenta
        banco = tarjeta.banco

        # Consultas optimizadas
        cuentas = CuentaBancaria.objects.filter(idBanco=id).annotate(
            fi=F("fechaIngreso"),
            ft=F("fechaTransaccion"),
            desc_alias=F("descripcion"),
            valor_alias=F("valor"),
            id_tarjeta=F("idBanco"),
            origen=Value("Cuenta Bancaria", output_field=CharField())
        ).values("id", "fi", "ft", "valor_alias", "desc_alias", "id_tarjeta", "origen")

        recepcionDePagos = RecepcionPago.objects.filter(id_tarjeta_bancaria=id).annotate(
            fi=F('fecha_ingreso'),
            ft=F('fecha_transaccion'),
            desc_alias=F('observacion'),
            valor_alias=F('valor'),
            id_tarjeta=F('id_tarjeta_bancaria'),
            origen=Value('Recepcion de Pago', output_field=CharField())
        ).values('id', 'fi', 'ft', 'valor_alias', 'desc_alias', 'id_tarjeta', 'origen')

        devoluciones = Devoluciones.objects.filter(id_tarjeta_bancaria=id).annotate(
            fi=F("fecha_ingreso"),
            ft=F("fecha_transaccion"),
            desc_alias=F("observacion"),
            valor_alias=F("valor"),
            id_tarjeta=F("id_tarjeta_bancaria"),
            origen=Value("Devolución", output_field=CharField())
        ).values("id", "fi", "ft", "valor_alias", "desc_alias", "id_tarjeta", "origen")

        gastos = Gastogenerales.objects.filter(id_tarjeta_bancaria=id).annotate(
            fi=F("fecha_ingreso"),
            ft=F("fecha_transaccion"),
            desc_alias=F("observacion"),
            valor_alias=F("valor"),
            id_tarjeta=F("id_tarjeta_bancaria"),
            origen=Value("Gasto General", output_field=CharField())
        ).values("id", "fi", "ft", "valor_alias", "desc_alias", "id_tarjeta", "origen")

        utilidadocacional = Utilidadocacional.objects.filter(id_tarjeta_bancaria=id).annotate(
            fi=F("fecha_ingreso"),
            ft=F("fecha_transaccion"),
            desc_alias=F("observacion"),
            valor_alias=F("valor"),
            id_tarjeta=F("id_tarjeta_bancaria"),
            origen=Value("Utilidad Ocasional", output_field=CharField())
        ).values("id", "fi", "ft", "valor_alias", "desc_alias", "id_tarjeta", "origen")

        # Unir todas las consultas
        union_result = list(cuentas) + list(recepcionDePagos) + list(devoluciones) + list(gastos) + list(utilidadocacional)

        # Crear DataFrame con los datos
        df = pd.DataFrame(union_result)

        # Renombrar columnas si hay datos
        if not df.empty:
            df.rename(columns={
                "fi": "Fecha Ingreso",
                "ft": "Fecha Transacción",
                "desc_alias": "Descripción",
                "valor_alias": "Valor",
                "id_tarjeta": "ID Tarjeta",
                "origen": "Tipo de Movimiento",
            }, inplace=True)

            # Formatear fechas si existen
            if "Fecha Ingreso" in df.columns:
                df["Fecha Ingreso"] = pd.to_datetime(df["Fecha Ingreso"]).dt.tz_localize(None)
            if "Fecha Transacción" in df.columns:
                df["Fecha Transacción"] = pd.to_datetime(df["Fecha Transacción"]).dt.tz_localize(None)

        # Calcular totales
        total_cuentas = safe_sum(CuentaBancaria.objects.filter(idBanco=id), "valor")
        total_devoluciones = safe_sum(Devoluciones.objects.filter(id_tarjeta_bancaria=id), "valor")
        total_gastos = safe_sum(Gastogenerales.objects.filter(id_tarjeta_bancaria=id), "valor")
        total_utilidad = safe_sum(Utilidadocacional.objects.filter(id_tarjeta_bancaria=id), "valor")
        total_recepcionDePagos = safe_sum(RecepcionPago.objects.filter(id_tarjeta_bancaria=id), "valor")
        total_general = total_cuentas + total_devoluciones + total_gastos + total_utilidad + total_recepcionDePagos

        # Crear DataFrame con los totales
        df_totales = pd.DataFrame({
            "Concepto": ["Total Cuenta Bancaria", "Total Devoluciones", "Total Gastos Generales", "Total Utilidad Ocasional", "Total Recepcion de pagos", "TOTAL GENERAL"],
            "Valor": [total_cuentas, total_devoluciones, total_gastos, total_utilidad, total_recepcionDePagos, total_general]
        })

        # Crear DataFrame con la información de la tarjeta
        df_tarjeta = pd.DataFrame({
            "Campo": ["Nombre Cuenta", "Descripción", "Número Cuenta", "Banco"],
            "Valor": [nombre_cuenta, descripcion, numero_cuenta, banco]
        })

        # Usar un archivo temporal para evitar problemas de concurrencia
        with NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            with pd.ExcelWriter(tmp.name, engine="xlsxwriter") as writer:
                df_tarjeta.to_excel(writer, sheet_name="Información Cuenta", index=False)
                df.to_excel(writer, sheet_name="Movimientos", index=False)
                df_totales.to_excel(writer, sheet_name="Totales", index=False)

            # Leer el archivo Excel y enviarlo como respuesta HTTP
            with open(tmp.name, "rb") as excel_file:
                response = HttpResponse(excel_file.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                response["Content-Disposition"] = f'attachment; filename="Reporte_Cuenta_{id}.xlsx"'

        return response

    except Exception as e:
        return Response({"error": f"Error interno: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
