from django.shortcuts import render
from django.http import HttpResponse
from .utils import render_to_pdf

from cuentasbancarias.models    import CuentaBancaria
from registroTarjetas.models    import RegistroTarjetas
from recepcionPago.models       import RecepcionPago
from devoluciones.models        import Devoluciones
from gastosgenerales.models     import Gastogenerales
from utilidadocacional.models   import Utilidadocacional
from django.db.models import F, Value, CharField, Sum

from decimal import Decimal
from datetime import datetime

def parse_date_with_defaults(date_str, is_end=False):
    if not date_str:
        return None
    
    parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
    if is_end:
        parsed_date = parsed_date.replace(hour=23, minute=59, second=59)
    else:
        parsed_date = parsed_date.replace(hour=0, minute=0, second=0)
    
    return parsed_date

# Create your views here.
def downloadpdf_view(request, id):
    # Obtener los parámetros de fecha de la URL
    fecha_inicio = request.GET.get('fechaInicio')
    fecha_fin    = request.GET.get('fechaFin')

    # Convertir las fechas a objetos de Python
    fecha_inicio = parse_date_with_defaults(fecha_inicio)
    fecha_fin    = parse_date_with_defaults(fecha_fin, is_end=True)

    if fecha_fin and fecha_fin:
            try:
                tarjeta = RegistroTarjetas.objects.get(pk=id)
                nombre_cuenta   = tarjeta.nombre_cuenta
                descripcion     = tarjeta.descripcion
                numero_cuenta   = tarjeta.numero_cuenta
                banco           = tarjeta.banco
            except:
                return HttpResponse({"error": "Tarjeta no encontrada"}, status=404)
            
            # Consulta para Cuentas Bancarias
            cuentas = CuentaBancaria.objects.filter(idBanco=id).annotate(
                fi=F('fechaIngreso'),
                ft=F('fechaTransaccion'),
                desc_alias=F('descripcion'),
                valor_alias=F('valor'),
                id_tarjeta=F('idBanco'),
                origen=Value('Cuenta Bancaria', output_field=CharField())
            ).values('id', 'fi', 'ft', 'valor_alias', 'desc_alias', 'id_tarjeta', 'origen')
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

            # Consulta para Devoluciones
            devoluciones = Devoluciones.objects.filter(id_tarjeta_bancaria=id).annotate(
                fi=F('fecha_ingreso'),
                ft=F('fecha_transaccion'),
                desc_alias=F('observacion'),
                valor_alias=F('valor'),
                id_tarjeta=F('id_tarjeta_bancaria'),
                origen=Value('Devolución', output_field=CharField())
            ).values('id', 'fi', 'ft', 'valor_alias', 'desc_alias', 'id_tarjeta', 'origen')
            devoluciones = devoluciones.filter(fi__range=(fecha_inicio, fecha_fin))

            # Consulta para Gastos Generales
            gastos = Gastogenerales.objects.filter(id_tarjeta_bancaria=id).annotate(
                fi=F('fecha_ingreso'),
                ft=F('fecha_transaccion'),
                desc_alias=F('observacion'),
                valor_alias=F('valor'),
                id_tarjeta=F('id_tarjeta_bancaria'),
                origen=Value('Gasto General', output_field=CharField())
            ).values('id', 'fi', 'ft', 'valor_alias', 'desc_alias', 'id_tarjeta', 'origen')
            gastos = gastos.filter(fi__range=(fecha_inicio, fecha_fin))

            # Consulta para Utilidad Ocasional
            utilidadocacional = Utilidadocacional.objects.filter(id_tarjeta_bancaria=id).annotate(
                fi=F('fecha_ingreso'),
                ft=F('fecha_transaccion'),
                desc_alias=F('observacion'),
                valor_alias=F('valor'),
                id_tarjeta=F('id_tarjeta_bancaria'),
                origen=Value('Utilidad Ocasional', output_field=CharField())
            ).values('id', 'fi', 'ft', 'valor_alias', 'desc_alias', 'id_tarjeta', 'origen')
            utilidadocacional = utilidadocacional.filter(fi__range=(fecha_inicio, fecha_fin))

            # Unir todas las consultas asegurando que los tipos coincidan
            union_result = list(cuentas.union(devoluciones, gastos, utilidadocacional, recepcionDePagos))

            # Calcular totales de cada categoría
            total_cuentas           = safe_sum( CuentaBancaria.objects.filter(idBanco=id).filter(fechaIngreso__range=(fecha_inicio, fecha_fin)), "valor")
            total_devoluciones      = safe_sum(Devoluciones.objects.filter(id_tarjeta_bancaria=id).filter(fecha_ingreso__range=(fecha_inicio, fecha_fin)), "valor")
            total_gastos            = safe_sum(Gastogenerales.objects.filter(id_tarjeta_bancaria=id).filter(fecha_ingreso__range=(fecha_inicio, fecha_fin)), "valor")
            total_utilidad          = safe_sum(Utilidadocacional.objects.filter(id_tarjeta_bancaria=id).filter(fecha_ingreso__range=(fecha_inicio, fecha_fin)), "valor")
            total_recepcionDePagos  = safe_sum(RecepcionPago.objects.filter(id_tarjeta_bancaria=id).filter(fecha_ingreso__range=(fecha_inicio, fecha_fin)), "valor")


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

            # Respuesta JSON combinando los datos y los totale
            pdf = render_to_pdf('download.html', response_data)
            return HttpResponse(pdf, content_type='application/pdf')

    try:
        tarjeta = RegistroTarjetas.objects.get(pk=id)
        nombre_cuenta   = tarjeta.nombre_cuenta
        descripcion     = tarjeta.descripcion
        numero_cuenta   = tarjeta.numero_cuenta
        banco           = tarjeta.banco
    except:
        return HttpResponse({"error": "Tarjeta no encontrada"}, status=404)
    
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

    # Respuesta JSON combinando los datos y los totale
    pdf = render_to_pdf('download.html', response_data)
    return HttpResponse(pdf, content_type='application/pdf')


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