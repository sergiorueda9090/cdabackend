# cuentas_bancarias/api/views.py
from datetime import datetime
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from registroTarjetas.models import RegistroTarjetas
from registroTarjetas.api.serializers import RegistroTarjetasSerializer

from cuentasbancarias.models  import CuentaBancaria
from recepcionPago.models     import RecepcionPago
from devoluciones.models      import Devoluciones
from gastos.models              import Gastos
from gastosgenerales.models   import Gastogenerales
from utilidadocacional.models import Utilidadocacional
from cotizador.models         import Cotizador
from clientes.models            import Cliente
from ajustesaldos.models        import Ajustesaldo
from fichaproveedor.models      import FichaProveedor

from gastosgenerales.api.serializers import GastogeneralesSerializer

from django.db import models
from django.db.models import Sum, F, Value, CharField, Sum, Q, FloatField
from django.db.models.functions import Replace, Cast, Coalesce


from rest_framework.permissions import IsAuthenticated
from users.decorators           import check_role
from django.db import transaction


def listar_gastos_generales(fecha_inicio=None, fecha_fin=None):
    try:
        # Parseo seguro de fechas
        if fecha_inicio:
            fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        if fecha_fin:
            fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d")
    except ValueError:
        print("Formato de fecha inválido.")
        return []

    try:
        # Base queryset
        gastos = Gastogenerales.objects.select_related('id_tipo_gasto', 'id_tarjeta_bancaria')

        # Aplicar filtro de fechas al modelo Gastos (al que está relacionado con id_tipo_gasto)
        if fecha_inicio and fecha_fin:
            gastos = gastos.filter(id_tipo_gasto__fecha_ingreso__range=(fecha_inicio, fecha_fin))

        total_gastos_data = []

        for gasto in gastos:
            try:
                tarjeta = gasto.id_tarjeta_bancaria
                gasto_model = gasto.id_tipo_gasto

                valor = abs(int(gasto.valor))

                total_gastos_data.append({
                    'nombre_cuenta': gasto_model.name,
                    'valor': valor,
                    'origen': 'gasto'
                })

            except Exception as e:
                print(f"Error procesando gasto ID {gasto.id}: {e}")
                continue

        return total_gastos_data

    except Exception as e:
        print(f"Error en la función listar_gastos_generales: {e}")
        return []
    
def get_all_ficha_cliente(fechaInicio=None, fechaFin=None):
    # Obtener parámetros de fecha
    fecha_inicio = fechaInicio
    fecha_fin    = fechaFin

    try:
        if fecha_inicio:
            fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        if fecha_fin:
            fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d")
    except ValueError:
        return Response({"error": "Formato de fecha inválido. Use YYYY-MM-DD."}, status=400)

    # Obtener cotizadores con sus idCliente
    cotizadores_qs = Cotizador.objects.exclude(precioDeLey__isnull=True).exclude(precioDeLey="").values('id', 'fechaCreacion', 'total', 'idCliente', 'placa', 'archivo')

    if fecha_inicio and fecha_fin:
        cotizadores_qs = cotizadores_qs.filter(fechaCreacion__range=[fecha_inicio, fecha_fin])

    # Obtener clientes en un diccionario {id: nombre}
    clientes_dict = {c['id']: c['nombre'] for c in Cliente.objects.values('id', 'nombre')}

    # Obtener valores de cuentas bancarias
    cuentasbancarias_qs = {c['idCotizador']: c['valor'] for c in CuentaBancaria.objects.values('idCotizador', 'valor')}

    # Formatear cotizadores
    cotizadores_list = [
        {
            'id': cotizador['id'],
            'fi': cotizador['fechaCreacion'],
            'ft': None,
            'valor_alias': cuentasbancarias_qs.get(cotizador['id'], "Desconocido"),
            'desc_alias': "",
            'cliente_nombre': clientes_dict.get(cotizador['idCliente'], "Desconocido"),
            'origen': "Tramites",
            'placa': cotizador['placa'],
            'archivo': cotizador['archivo'],
        }
        for cotizador in cotizadores_qs
        if cuentasbancarias_qs.get(cotizador['id']) is not None and clientes_dict.get(cotizador['idCliente']) is not None
    ]

    # Filtros de fecha para los demás modelos
    filtros_fecha = {}
    if fecha_inicio and fecha_fin:
        filtros_fecha = {'fecha_ingreso__range': [fecha_inicio, fecha_fin]}

    recepcionDePagos = list(RecepcionPago.objects.select_related('cliente')
        .filter(**filtros_fecha)
        .annotate(
            fi=F('fecha_ingreso'),
            ft=F('fecha_transaccion'),
            valor_alias=F('valor'),
            desc_alias=F('observacion'),
            cliente_nombre=F('cliente__nombre'),
            origen=Value("Recepcion de Pago", output_field=CharField()),
            placa=Value("", output_field=CharField()),
            archivo=Value("", output_field=CharField()),
        ).values('id', 'fi', 'ft', 'valor_alias', 'desc_alias', 'cliente_nombre', 'origen', 'placa', 'archivo'))

    devoluciones = list(Devoluciones.objects.select_related('id_cliente')
        .filter(**filtros_fecha)
        .annotate(
            fi=F('fecha_ingreso'),
            ft=F('fecha_transaccion'),
            valor_alias=F('valor'),
            desc_alias=F('observacion'),
            cliente_nombre=F('id_cliente__nombre'),
            origen=Value("Devoluciones", output_field=CharField()),
            placa=Value("", output_field=CharField()),
            archivo=Value("", output_field=CharField()),
        ).values('id', 'fi', 'ft', 'valor_alias', 'desc_alias', 'cliente_nombre', 'origen', 'placa', 'archivo'))

    ajuestesSaldos = list(Ajustesaldo.objects.select_related('id_cliente')
        .filter(**filtros_fecha)
        .annotate(
            fi=F('fecha_ingreso'),
            ft=F('fecha_transaccion'),
            valor_alias=F('valor'),
            desc_alias=F('observacion'),
            cliente_nombre=F('id_cliente__nombre'),
            origen=Value("Ajustes de Saldos", output_field=CharField()),
            placa=Value("", output_field=CharField()),
            archivo=Value("", output_field=CharField()),
        ).values('id', 'fi', 'ft', 'valor_alias', 'desc_alias', 'cliente_nombre', 'origen', 'placa', 'archivo'))

    # Unir todos los resultados
    union_result = cotizadores_list + recepcionDePagos + devoluciones + ajuestesSaldos

    # Filtrar solo los campos necesarios
    resultado_filtrado = [
        {   
            'nombre_cuenta' : item['cliente_nombre'],
            'valor'         : item['valor_alias'],
            'origen'        : 'Clientes'
        }
        for item in union_result
    ]

    return resultado_filtrado

def get_all_fecha_proveedores(fecha_inicio=None, fecha_fin=None):
    fecha_inicio = fecha_inicio
    fecha_fin    = fecha_fin

    try:
        if fecha_inicio:
            fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        if fecha_fin:
            fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d")
    except ValueError:
        # Retorna vacío si hay error en fechas
        return []

    proveedores_qs = FichaProveedor.objects.all()

    if fecha_inicio and fecha_fin:
        proveedores_qs = proveedores_qs.filter(fechaCreacion__range=[fecha_inicio, fecha_fin])

    agrupado = proveedores_qs.values(
        'idproveedor__id',
        'idproveedor__nombre',
        'idcotizador__etiquetaDos'
    ).annotate(
        total_comision=Coalesce(
            Sum(Cast('comisionproveedor', output_field=FloatField())), 0.0
        )
    )

    resultado = [
        {
            "nombre_cuenta": item['idproveedor__nombre'],
            "valor": round(item['total_comision'], 2),
            "origen": "fichaproveedor"
        }
        for item in agrupado
    ]

    return resultado


def safe_to_float(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1,2)
def obtener_balancegeneral(request):

    fecha_inicio = request.GET.get('fechaInicio')
    fecha_fin    = request.GET.get('fechaFin')

    try:
        if fecha_inicio:
            fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        if fecha_fin:
            fecha_fin    = datetime.strptime(fecha_fin, "%Y-%m-%d")
    except ValueError:
        return Response({"error": "Formato de fecha inválido. Use YYYY-MM-DD."}, status=400)
    # Verificar si todas las tablas existen antes de ejecutar consultas
    required_models = {
        "RegistroTarjetas"  : RegistroTarjetas,
        "RecepcionPago"     : RecepcionPago,
        "Devoluciones"      : Devoluciones,
        "Gastogenerales"    : Gastogenerales,
        "Utilidadocacional" : Utilidadocacional
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
        serializer.data[i]['origen'] = 'tarjetas'

    # ✅ Llamar a la función que devuelve valores de clientes
    valores_clientes = get_all_ficha_cliente(fecha_inicio, fecha_fin)
    valores_gastos   = listar_gastos_generales(fecha_inicio, fecha_fin)
    fichas_proveedor = get_all_fecha_proveedores(fecha_inicio, fecha_fin)
    
    
    total_saldo_clientes = sum(safe_to_float(item['valor']) for item in valores_clientes)
    total_gastos_generales = sum(safe_to_float(item['valor']) for item in valores_gastos)
    total_comisiones_proveedores = sum(safe_to_float(item['valor']) for item in fichas_proveedor)
    total_tarjetas = sum(item['valor'] for item in serializer.data if isinstance(item['valor'], (int, float)))
    
    # 🔢 Suma total de todos los valores
    suma_total = (
        total_saldo_clientes +
        total_gastos_generales +
        total_comisiones_proveedores +
        total_tarjetas
    )
    print("suma_total ",suma_total)
    # ✅ Armar respuesta final uniendo ambos resultados
    respuesta_final = serializer.data + valores_clientes + valores_gastos + fichas_proveedor
    return Response({
        "datos": respuesta_final,
        "total_saldo_clientes": total_saldo_clientes,
        "total_gastos_generales": total_gastos_generales,
        "total_comisiones_proveedores": total_comisiones_proveedores,
        'totalTarjetas': total_tarjetas,
        "sumaTotal": suma_total
    }, status=status.HTTP_200_OK)

