from django.shortcuts import render
import pandas as pd
# cuentas_bancarias/api/views.py
from django.utils.dateparse import parse_date

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

    recepcionDePagos = RecepcionPago.objects.all().annotate(
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
    print("id {}".format(id))
    fecha_inicio = request.GET.get('fechaInicio')
    fecha_fin = request.GET.get('fechaFin')


    # Convertir las fechas a objetos de Python
    fecha_inicio = parse_date(fecha_inicio) if fecha_inicio else None
    fecha_fin = parse_date(fecha_fin) if fecha_fin else None

    print("id {}".format(id))
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
        tarjeta = RegistroTarjetas.objects.get(pk=id)
        nombre_cuenta   = tarjeta.nombre_cuenta
        descripcion     = tarjeta.descripcion
        numero_cuenta   = tarjeta.numero_cuenta
        banco           = tarjeta.banco
    except RegistroTarjetas.DoesNotExist:
        return Response({"error": "Tarjeta no encontrada"}, status=status.HTTP_404_NOT_FOUND)
    
    # Consulta para Cuentas Bancarias
    cuentas = CuentaBancaria.objects.filter(idBanco=id).annotate(
        fi=F("fechaIngreso"),
        ft=F("fechaTransaccion"),
        desc_alias=F("descripcion"),
        valor_alias=F("valor"),
        id_tarjeta=F("idBanco"),
        origen=Value("Cuenta Bancaria", output_field=CharField())
    ).values("id", "fi", "ft", "valor_alias", "desc_alias", "id_tarjeta", "origen")

    recepcionDePagos = RecepcionPago.objects.all().annotate(
        fi=F('fecha_ingreso'),
        ft=F('fecha_transaccion'),
        desc_alias=F('observacion'),
        valor_alias=F('valor'),
        id_tarjeta=F('id_tarjeta_bancaria'),
        origen=Value('Recepcion de Pago', output_field=CharField())
    ).values('id', 'fi', 'ft', 'valor_alias', 'desc_alias', 'id_tarjeta', 'origen')

    # Consulta para Devoluciones
    devoluciones = Devoluciones.objects.filter(id_tarjeta_bancaria=id).annotate(
        fi=F("fecha_ingreso"),
        ft=F("fecha_transaccion"),
        desc_alias=F("observacion"),
        valor_alias=F("valor"),
        id_tarjeta=F("id_tarjeta_bancaria"),
        origen=Value("Devolución", output_field=CharField())
    ).values("id", "fi", "ft", "valor_alias", "desc_alias", "id_tarjeta", "origen")

    # Consulta para Gastos Generales
    gastos = Gastogenerales.objects.filter(id_tarjeta_bancaria=id).annotate(
        fi=F("fecha_ingreso"),
        ft=F("fecha_transaccion"),
        desc_alias=F("observacion"),
        valor_alias=F("valor"),
        id_tarjeta=F("id_tarjeta_bancaria"),
        origen=Value("Gasto General", output_field=CharField())
    ).values("id", "fi", "ft", "valor_alias", "desc_alias", "id_tarjeta", "origen")

    # Consulta para Utilidad Ocasional
    utilidadocacional = Utilidadocacional.objects.filter(id_tarjeta_bancaria=id).annotate(
        fi=F("fecha_ingreso"),
        ft=F("fecha_transaccion"),
        desc_alias=F("observacion"),
        valor_alias=F("valor"),
        id_tarjeta=F("id_tarjeta_bancaria"),
        origen=Value("Utilidad Ocasional", output_field=CharField())
    ).values("id", "fi", "ft", "valor_alias", "desc_alias", "id_tarjeta", "origen")

    # Unir todas las consultas
    union_result = list(cuentas.union(devoluciones, gastos, utilidadocacional, recepcionDePagos))

    # Crear DataFrame con los datos
    df = pd.DataFrame(list(union_result))

    # Si hay datos, formatear las fechas quitando la zona horaria
    if not df.empty:
        df.rename(columns={
            "fi": "Fecha Ingreso",
            "ft": "Fecha Transacción",
            "desc_alias": "Descripción",
            "valor_alias": "Valor",
            "id_tarjeta": "ID Tarjeta",
            "origen": "Tipo de Movimiento",
        }, inplace=True)

        # Eliminar zona horaria de las fechas si existen
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
        "Concepto": ["Total Cuenta Bancaria", "Total Devoluciones", "Total Gastos Generales", "Total Utilidad Ocasional", "Total Recepcion de pagos" ,"TOTAL GENERAL"],
        "Valor": [total_cuentas, total_devoluciones, total_gastos, total_utilidad, total_recepcionDePagos, total_general]
    })

    # Crear DataFrame con la información de la tarjeta
    df_tarjeta = pd.DataFrame({
        "Campo": ["Nombre Cuenta", "Descripción", "Número Cuenta", "Banco"],
        "Valor": [nombre_cuenta, descripcion, numero_cuenta, banco]
    })

    # Crear un archivo Excel con múltiples hojas
    with pd.ExcelWriter("Reporte_Cuenta.xlsx", engine="xlsxwriter") as writer:
        df_tarjeta.to_excel(writer, sheet_name="Información Cuenta", index=False)
        df.to_excel(writer, sheet_name="Movimientos", index=False)
        df_totales.to_excel(writer, sheet_name="Totales", index=False)

    # Leer el archivo Excel y enviarlo como respuesta HTTP
    with open("Reporte_Cuenta.xlsx", "rb") as excel_file:
        response = HttpResponse(excel_file.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = f'attachment; filename="Reporte_Cuenta_{id}.xlsx"'
    
    return response


@api_view(["GET"])
def download_report_pdf(request, id):
    pass