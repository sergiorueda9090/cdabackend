# cuentas_bancarias/api/views.py
from datetime import datetime
from django.shortcuts import get_object_or_404
from decimal import Decimal
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
from cargosnoregistrados.models import Cargosnodesados

from gastosgenerales.api.serializers import GastogeneralesSerializer

from django.db import models
from django.db.models import Sum, F, Value, CharField, Sum, Q, FloatField
from django.db.models.functions import Replace, Cast, Coalesce


from rest_framework.permissions import IsAuthenticated
from users.decorators           import check_role
from django.db import transaction

from tarjetastrasladofondo.models import Tarjetastrasladofondo

import math

def listar_gastos_generales(fecha_inicio=None, fecha_fin=None):
    try:
        if fecha_inicio and isinstance(fecha_inicio, str):
            fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        else:
            fecha_inicio = fecha_inicio

        if fecha_fin and isinstance(fecha_fin, str):
            fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d")
        else:
            fecha_fin = fecha_fin
    except ValueError:
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
    
# def get_all_ficha_cliente(fechaInicio=None, fechaFin=None):
#     # Obtener parámetros de fecha
#     fecha_inicio = fechaInicio
#     fecha_fin    = fechaFin

#     try:
#         if fechaInicio and isinstance(fechaInicio, str):
#             fecha_inicio = datetime.strptime(fechaInicio, "%Y-%m-%d")
#         else:
#             fecha_inicio = fechaInicio

#         if fechaFin and isinstance(fechaFin, str):
#             fecha_fin = datetime.strptime(fechaFin, "%Y-%m-%d")
#         else:
#             fecha_fin = fechaFin

#     except ValueError:
#         return []

#     # Obtener cotizadores con sus idCliente
#     cotizadores_qs = Cotizador.objects.exclude(precioDeLey__isnull=True).exclude(precioDeLey="").values('id', 'fechaCreacion', 'total', 'idCliente', 'placa', 'archivo')

#     if fecha_inicio and fecha_fin:
#         cotizadores_qs = cotizadores_qs.filter(fechaCreacion__range=[fecha_inicio, fecha_fin])

#     # Obtener clientes en un diccionario {id: nombre}
#     clientes_dict = {c['id']: c['nombre'] for c in Cliente.objects.values('id', 'nombre')}

#     # Obtener valores de cuentas bancarias
#     cuentasbancarias_qs = {c['idCotizador']: c['valor'] for c in CuentaBancaria.objects.values('idCotizador', 'valor')}

#     # Formatear cotizadores
#     cotizadores_list = [
#         {
#             'id': cotizador['id'],
#             'fi': cotizador['fechaCreacion'],
#             'ft': None,
#             'valor_alias': cuentasbancarias_qs.get(cotizador['id'], "Desconocido"),
#             'desc_alias': "",
#             'cliente_nombre': clientes_dict.get(cotizador['idCliente'], "Desconocido"),
#             'origen': "Tramites",
#             'placa': cotizador['placa'],
#             'archivo': cotizador['archivo'],
#             'total': -abs(safe_to_float(cotizador['total']))
#         }
#         for cotizador in cotizadores_qs
#         if cuentasbancarias_qs.get(cotizador['id']) is not None and clientes_dict.get(cotizador['idCliente']) is not None
#     ]

#     # Filtros de fecha para los demás modelos
#     filtros_fecha = {}
#     if fecha_inicio and fecha_fin:
#         filtros_fecha = {'fecha_ingreso__range': [fecha_inicio, fecha_fin]}

#     recepcionDePagos = list(RecepcionPago.objects.select_related('cliente')
#         .filter(**filtros_fecha)
#         .annotate(
#             fi=F('fecha_ingreso'),
#             ft=F('fecha_transaccion'),
#             valor_alias=F('valor'),
#             desc_alias=F('observacion'),
#             cliente_nombre=F('cliente__nombre'),
#             origen=Value("Recepcion de Pago", output_field=CharField()),
#             placa=Value("", output_field=CharField()),
#             archivo=Value("", output_field=CharField()),
#             total=F('valor'),
#         ).values('id', 'fi', 'ft', 'valor_alias', 'desc_alias', 'cliente_nombre', 'origen', 'placa', 'archivo', 'total'))

#     devoluciones = list(Devoluciones.objects.select_related('id_cliente')
#         .filter(**filtros_fecha)
#         .annotate(
#             fi=F('fecha_ingreso'),
#             ft=F('fecha_transaccion'),
#             valor_alias=F('valor'),
#             desc_alias=F('observacion'),
#             cliente_nombre=F('id_cliente__nombre'),
#             origen=Value("Devoluciones", output_field=CharField()),
#             placa=Value("", output_field=CharField()),
#             archivo=Value("", output_field=CharField()),
#             total=F('valor'),
#         ).values('id', 'fi', 'ft', 'valor_alias', 'desc_alias', 'cliente_nombre', 'origen', 'placa', 'archivo', 'total'))

#     ajuestesSaldos = list(Ajustesaldo.objects.select_related('id_cliente')
#         .filter(**filtros_fecha)
#         .annotate(
#             fi=F('fecha_ingreso'),
#             ft=F('fecha_transaccion'),
#             valor_alias=F('valor'),
#             desc_alias=F('observacion'),
#             cliente_nombre=F('id_cliente__nombre'),
#             origen=Value("Ajustes de Saldos", output_field=CharField()),
#             placa=Value("", output_field=CharField()),
#             archivo=Value("", output_field=CharField()),
#             total=F('valor'),
#         ).values('id', 'fi', 'ft', 'valor_alias', 'desc_alias', 'cliente_nombre', 'origen', 'placa', 'archivo', 'total'))

#     cargosNoDeseados = list(
#         Cargosnodesados.objects.select_related('id_cliente')
#         .filter(**filtros_fecha)
#         .annotate(
#             fi=F('fecha_ingreso'),
#             ft=F('fecha_transaccion'),
#             valor_alias=F('valor'),
#             desc_alias=F('observacion'),
#             cliente_nombre=F('id_cliente__nombre'),
#             origen=Value("Cargos no deseados", output_field=CharField()),
#             placa=Value("", output_field=CharField()),
#             archivo=Value("", output_field=CharField()),
#             total=F('valor'),
#         ).values('id', 'fi', 'ft', 'valor_alias', 'desc_alias', 'cliente_nombre', 'origen', 'placa', 'archivo', 'total')
#     )

#     # Unir todos los resultados
#     union_result = cotizadores_list + recepcionDePagos + devoluciones + ajuestesSaldos + cargosNoDeseados

#     # Filtrar solo los campos necesarios
#     resultado_filtrado = [
#         {   
#             'nombre_cuenta' : item['cliente_nombre'],
#             'valor'         : item['valor_alias'],
#             'origen'        : f"Cliente - {item['origen']}",
#             'total'         : item['total'] if 'total' in item else 0
#         }
#         for item in union_result
#     ]

#     return resultado_filtrado

def get_all_ficha_cliente(fechaInicio=None, fechaFin=None): 
    fecha_inicio = fechaInicio
    fecha_fin = fechaFin

    try:
        if fechaInicio and isinstance(fechaInicio, str):
            fecha_inicio = datetime.strptime(fechaInicio, "%Y-%m-%d")
        if fechaFin and isinstance(fechaFin, str):
            fecha_fin = datetime.strptime(fechaFin, "%Y-%m-%d")
    except ValueError:
        return []

    # ✅ Traer todos los cotizadores (sin excluir por precioDeLey, ni idBanco)
    cotizadores_qs = Cotizador.objects.values(
        'id', 'fechaCreacion', 'total', 'idCliente', 'placa', 'archivo', 'idBanco', 'precioDeLey'
    )

    if fecha_inicio and fecha_fin:
        cotizadores_qs = cotizadores_qs.filter(fechaCreacion__range=[fecha_inicio, fecha_fin])

    # Obtener clientes en un diccionario {id: nombre}
    clientes_dict = {c['id']: c['nombre'] for c in Cliente.objects.values('id', 'nombre')}

    # Obtener valores de cuentas bancarias
    cuentasbancarias_qs = {c['idCotizador']: c['valor'] for c in CuentaBancaria.objects.values('idCotizador', 'valor')}

    #Ya no se excluye ningún cotizador, incluso si falta cliente o cuenta bancaria
    cotizadores_list = []
    for cotizador in cotizadores_qs:
        # Convertir total de forma segura
        total_valor = safe_to_float(cotizador['total'])
        if not isinstance(total_valor, (int, float)) or math.isnan(total_valor):
            total_valor = 0.0  # Valor por defecto si es NaN o inválido

        valor_alias = cuentasbancarias_qs.get(cotizador['id'], None)

        # Si no existe valor_alias o es None, usar precioDeLey
        if valor_alias is None:
            valor_alias = cotizador.get('precioDeLey', 0.0)
            valor_alias = str(valor_alias).replace('.', '').replace(',', '')
            try:
                valor_alias = -abs(float(valor_alias))
            except ValueError:
                valor_alias = 0.0


        cotizadores_list.append({
            'id': cotizador['id'],
            'fi': cotizador['fechaCreacion'],
            'ft': None,
            'valor_alias': valor_alias,
            'desc_alias': "",
            'cliente_nombre': clientes_dict.get(cotizador['idCliente'], "Desconocido"),
            'origen': "Tramites",
            'placa': cotizador['placa'],
            'archivo': cotizador['archivo'],
            'idBanco': cotizador['idBanco'],
            'total': -abs(total_valor),  # siempre numérico
        })

    filtros_fecha = {}
    if fecha_inicio and fecha_fin:
        filtros_fecha = {'fecha_ingreso__range': [fecha_inicio, fecha_fin]}

    recepcionDePagos = list(
        RecepcionPago.objects.select_related('cliente')
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
            total=F('valor'),
        )
        .values('id', 'fi', 'ft', 'valor_alias', 'desc_alias', 'cliente_nombre', 'origen', 'placa', 'archivo', 'total')
    )

    devoluciones = list(
        Devoluciones.objects.select_related('id_cliente')
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
            total=F('valor'),
        )
        .values('id', 'fi', 'ft', 'valor_alias', 'desc_alias', 'cliente_nombre', 'origen', 'placa', 'archivo', 'total')
    )

    ajuestesSaldos = list(
        Ajustesaldo.objects.select_related('id_cliente')
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
            total=F('valor'),
        )
        .values('id', 'fi', 'ft', 'valor_alias', 'desc_alias', 'cliente_nombre', 'origen', 'placa', 'archivo', 'total')
    )

    cargosNoDeseados = list(
        Cargosnodesados.objects.select_related('id_cliente')
        .filter(**filtros_fecha)
        .annotate(
            fi=F('fecha_ingreso'),
            ft=F('fecha_transaccion'),
            valor_alias=F('valor'),
            desc_alias=F('observacion'),
            cliente_nombre=F('id_cliente__nombre'),
            origen=Value("Cargos no deseados", output_field=CharField()),
            placa=Value("", output_field=CharField()),
            archivo=Value("", output_field=CharField()),
            total=F('valor'),
        )
        .values('id', 'fi', 'ft', 'valor_alias', 'desc_alias', 'cliente_nombre', 'origen', 'placa', 'archivo', 'total')
    )

    # Unir todos los resultados
    union_result = cotizadores_list + recepcionDePagos + devoluciones + ajuestesSaldos + cargosNoDeseados

    # Resultado final
    resultado_filtrado = [
        {   
            'nombre_cuenta': item['cliente_nombre'],
            'valor': item['valor_alias'],
            'origen': f"Cliente - {item['origen']}",
            'total': item.get('total', 0),
            'idBanco': item.get('idBanco', None),  # 👈 Incluido para mostrar aunque sea null
        }
        for item in union_result
    ]

    return resultado_filtrado

def get_all_fecha_proveedores(fecha_inicio=None, fecha_fin=None):
    fecha_inicio = fecha_inicio
    fecha_fin    = fecha_fin

    try:
        if fecha_inicio and isinstance(fecha_inicio, str):
            fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        else:
            fecha_inicio = fecha_inicio

        if fecha_fin and isinstance(fecha_fin, str):
            fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d")
        else:
            fecha_fin = fecha_fin

    except ValueError:
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

def get_ficha_utilidades(fecha_inicio=None, fecha_fin=None):
    try:
        if fecha_inicio and isinstance(fecha_inicio, str):
            fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        else:
            fecha_inicio = fecha_inicio

        if fecha_fin and isinstance(fecha_fin, str):
            fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d")
        else:
            fecha_fin = fecha_fin

    except ValueError:
        return [{"valor": 0.0, "origen": "utilidades", "error": "Formato de fecha inválido"}]


    proveedores_qs = FichaProveedor.objects.all()

    if fecha_inicio and fecha_fin:
        proveedores_qs = proveedores_qs.filter(fechaCreacion__range=[fecha_inicio, fecha_fin])
    else:
        hoy = datetime.now().date()
        #proveedores_qs = proveedores_qs.filter(fechaCreacion__date=hoy)

    def safe_abs(value):
        try:
            return abs(float(value))
        except (ValueError, TypeError):
            return 0.0

    total_sum = sum([safe_abs(ficha.comisionproveedor) for ficha in proveedores_qs])

    return [{
        "valor": round(total_sum, 2),
        "origen": "utilidades"
    }]


def safe_to_float(value):
    try:
        # Si viene vacío o None, devolvemos 0
        if value in [None, "", " ", "null", "NaN"]:
            return 0.0
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def obtener_datos_cuenta(fecha_inicio=None, fecha_fin=None):
    """
    Calcula el total del 4x1000 considerando todas las cuentas y modelos relacionados.
    Si se especifican fechas, filtra por rango; si no, trae todo.
    """

    # -----------------------------------------------------------
    # 1️⃣ Conversión de fechas opcional
    # -----------------------------------------------------------
    try:
        if fecha_inicio and isinstance(fecha_inicio, str):
            fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        if fecha_fin and isinstance(fecha_fin, str):
            fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d")
    except ValueError:
        print("⚠️ Fechas inválidas, se ignorará el filtro de fechas.")
        fecha_inicio = None
        fecha_fin = None

    # -----------------------------------------------------------
    # 2️⃣ Helper para aplicar filtros de fechas dinámicos
    # -----------------------------------------------------------
    def apply_date_filter(queryset, field_name):
        if fecha_inicio and fecha_fin:
            return queryset.filter(**{f"{field_name}__range": [fecha_inicio, fecha_fin]})
        elif fecha_inicio:
            return queryset.filter(**{f"{field_name}__gte": fecha_inicio})
        elif fecha_fin:
            return queryset.filter(**{f"{field_name}__lte": fecha_fin})
        return queryset

    # -----------------------------------------------------------
    # 3️⃣ Consultas base
    # -----------------------------------------------------------
    base_fields = ('id', 'cuatro_por_mil')

    cuentas = apply_date_filter(CuentaBancaria.objects.all(), "fechaTransaccion").values(*base_fields)
    recepcionDePagos = apply_date_filter(RecepcionPago.objects.all(), "fecha_transaccion").values(*base_fields)
    devoluciones = apply_date_filter(Devoluciones.objects.all(), "fecha_transaccion").values(*base_fields)
    cargosNoRegistrados = apply_date_filter(Cargosnodesados.objects.all(), "fecha_transaccion").values(*base_fields)
    gastos = apply_date_filter(Gastogenerales.objects.all(), "fecha_transaccion").values(*base_fields)
    utilidadocacional = apply_date_filter(Utilidadocacional.objects.all(), "fecha_transaccion").values(*base_fields)

    # -----------------------------------------------------------
    # 4️⃣ Unión de todos los resultados
    # -----------------------------------------------------------
    union_result = (
        list(cuentas)
        + list(recepcionDePagos)
        + list(devoluciones)
        + list(cargosNoRegistrados)
        + list(gastos)
        + list(utilidadocacional)
    )

    # -----------------------------------------------------------
    # 5️⃣ Cálculo del total del 4x1000
    # -----------------------------------------------------------
    def to_number_4xmil(value):
        """Convierte el valor del 4xmil (que puede ser string con puntos/comas) a entero."""
        if value in [None, "", "0", "None"]:
            return 0
        try:
            return int(str(value).replace(".", "").replace(",", "").strip())
        except ValueError:
            return 0

    total_cuatro_por_mil_raw = sum(
        to_number_4xmil(item.get("cuatro_por_mil")) for item in union_result
    )

    # Convertimos a Decimal y garantizamos signo negativo
    total_cuatro_por_mil_final = Decimal(-abs(total_cuatro_por_mil_raw))

    # -----------------------------------------------------------
    # 6️⃣ Retorno final
    # -----------------------------------------------------------
    return total_cuatro_por_mil_final or Decimal(0)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1,2)
def obtener_balancegeneral(request):
    fecha_inicio = request.GET.get('fechaInicio')
    fecha_fin    = request.GET.get('fechaFin')

    try:
        if fecha_inicio:
            fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
            fecha_inicio = fecha_inicio.replace(hour=0, minute=0, second=0)
        if fecha_fin:
            fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d")
            fecha_fin = fecha_fin.replace(hour=23, minute=59, second=59)
    except ValueError:
        return Response({"error": "Formato de fecha inválido. Use YYYY-MM-DD."}, status=400)
    # Verificar si todas las tablas existen antes de ejecutar consultas
    required_models = {
        "RegistroTarjetas"  : RegistroTarjetas,
        "RecepcionPago"     : RecepcionPago,
        "Devoluciones"      : Devoluciones,
        "Gastogenerales"    : Gastogenerales,
        "Utilidadocacional" : Utilidadocacional,
        "Cargosnodesados"   : Cargosnodesados
    }

    missing_tables = [name for name, model in required_models.items() if not model._meta.db_table]

    if missing_tables:
        return Response(
            {"error": "Algunas tablas no existen en la base de datos", "tablas_faltantes": missing_tables},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    cuentas     = RegistroTarjetas.objects.all()
    serializer  = RegistroTarjetasSerializer(cuentas, many=True)
    tarjetas_info = []

        # >>> función corregida: ahora acepta queryset y nombre de campo
    def sumar_valores(queryset, campo="valor"):
        # Usa F(campo) para permitir campo dinámico
        return queryset.aggregate(
            total_suma=Sum(
                Cast(
                    Replace(F(campo), Value('.'), Value('')),
                    output_field=models.BigIntegerField()
                )
            )
        )['total_suma'] or 0
    # <<<

    for i in range(len(serializer.data)):

        tarjeta_nombre = serializer.data[i]['nombre_cuenta']
        tarjeta_id = serializer.data[i]['id']

        rtaCuentaBancaria = CuentaBancaria.objects.filter(
            idBanco=tarjeta_id
        ).aggregate(
            total_suma=Sum(
                Cast(Replace(F('valor'), Value('.'), Value('')), output_field=models.IntegerField())
            )
        )

        rtaRecepcionPago = RecepcionPago.objects.filter(
            id_tarjeta_bancaria=tarjeta_id
        ).aggregate(
            total_suma=Sum(
                Cast(Replace(F('valor'), Value('.'), Value('')), output_field=models.IntegerField())
            )
        )

        rtaDevoluciones = Devoluciones.objects.filter(
            id_tarjeta_bancaria=tarjeta_id
        ).aggregate(
            total_suma=Sum(
                Cast(Replace(F('valor'), Value('.'), Value('')), output_field=models.IntegerField())
            )
        )

        rtaGastogenerales = Gastogenerales.objects.filter(
            id_tarjeta_bancaria=tarjeta_id
        ).aggregate(
            total_suma=Sum(
                Cast(Replace(F('valor'), Value('.'), Value('')), output_field=models.IntegerField())
            )
        )

        rtaUtilidadocacional = Utilidadocacional.objects.filter(
            id_tarjeta_bancaria=tarjeta_id
        ).aggregate(
            total_suma=Sum(
                Cast(Replace(F('valor'), Value('.'), Value('')), output_field=models.IntegerField())
            )
        )

        rtaTarjetastrasladofondoResta = Tarjetastrasladofondo.objects.filter(
            id_tarjeta_bancaria_envia=tarjeta_id
        ).aggregate(
            total_suma=Sum(
                Cast(Replace(F('valor'), Value('.'), Value('')), output_field=models.IntegerField())
            )
        )

        rtaTarjetastrasladofondoSuma = Tarjetastrasladofondo.objects.filter(
            id_tarjeta_bancaria_recibe=tarjeta_id
        ).aggregate(
            total_suma=Sum(
                Cast(Replace(F('valor'), Value('.'), Value('')), output_field=models.IntegerField())
            )
        )

        # Nuevo agregado para Cargos no registrados
        rtaCargosNoDeseados = Cargosnodesados.objects.filter(
            id_tarjeta_bancaria=tarjeta_id
        ).aggregate(
            total_suma=Sum(
                Cast(Replace(F('valor'), Value('.'), Value('')), output_field=models.IntegerField())
            )
        )
        # Fin nuevo agregado
    
        cuatro_por_mil_cuentas      = sumar_valores(CuentaBancaria.objects.filter(idBanco=serializer.data[i]['id']), "cuatro_por_mil")
        cuatro_por_mil_recepciones  = sumar_valores(RecepcionPago.objects.filter(id_tarjeta_bancaria=serializer.data[i]['id']), "cuatro_por_mil")
        cuatro_por_mil_devoluciones = sumar_valores(Devoluciones.objects.filter(id_tarjeta_bancaria=serializer.data[i]['id']), "cuatro_por_mil")
        cuatro_por_mil_gastos       = sumar_valores(Gastogenerales.objects.filter(id_tarjeta_bancaria=serializer.data[i]['id']), "cuatro_por_mil")
        cuatro_por_mil_utilidad     = sumar_valores(Utilidadocacional.objects.filter(id_tarjeta_bancaria=serializer.data[i]['id']), "cuatro_por_mil")

        total_cuatro_por_mil = abs(
            cuatro_por_mil_cuentas + cuatro_por_mil_recepciones + cuatro_por_mil_devoluciones +
            cuatro_por_mil_gastos + cuatro_por_mil_utilidad
        )

        rtaCuentaBancaria['total_suma']      = rtaCuentaBancaria['total_suma']    if rtaCuentaBancaria['total_suma']     is not None else 0
        rtaRecepcionPago['total_suma']       = rtaRecepcionPago['total_suma']     if rtaRecepcionPago['total_suma']      is not None else 0
        rtaDevoluciones['total_suma']        = rtaDevoluciones['total_suma']      if rtaDevoluciones['total_suma']       is not None else 0
        rtaGastogenerales['total_suma']      = rtaGastogenerales['total_suma']    if rtaGastogenerales['total_suma']     is not None else 0
        rtaUtilidadocacional['total_suma']   = rtaUtilidadocacional['total_suma'] if rtaUtilidadocacional['total_suma']  is not None else 0  
        rtaTarjetastrasladofondoResta['total_suma'] = rtaTarjetastrasladofondoResta['total_suma'] if rtaTarjetastrasladofondoResta['total_suma'] is not None else 0
        rtaTarjetastrasladofondoSuma['total_suma'] = rtaTarjetastrasladofondoSuma['total_suma'] if rtaTarjetastrasladofondoSuma['total_suma'] is not None else 0
        rtaCargosNoDeseados['total_suma']    = rtaCargosNoDeseados['total_suma']  if rtaCargosNoDeseados['total_suma']   is not None else 0

        total_general = (
                rtaCuentaBancaria['total_suma']         +
                rtaRecepcionPago['total_suma']          +
                rtaDevoluciones['total_suma']           +
                rtaGastogenerales['total_suma']         + # <-- SUMA
                rtaUtilidadocacional['total_suma']      +
                
                - rtaTarjetastrasladofondoResta['total_suma'] + # <-- RESTA
                rtaTarjetastrasladofondoSuma['total_suma']  + # <-- SUMA
                rtaCargosNoDeseados['total_suma']           + # <-- SUMA

                - total_cuatro_por_mil
        )

        # Añadir a lista para respuesta
        tarjetas_info.append({"nombre": tarjeta_nombre, "valor" :total_general, "cuatro_por_mil": -total_cuatro_por_mil})
              
        serializer.data[i]['valor'] = total_general
        serializer.data[i]['origen'] = 'tarjetas'

    #Llamar a la función que devuelve valores de clientes
    valores_clientes = get_all_ficha_cliente() #(fecha_inicio, fecha_fin

    valores_gastos   = listar_gastos_generales(fecha_inicio, fecha_fin)
    fichas_proveedor = get_all_fecha_proveedores(fecha_inicio, fecha_fin)
    utilidades       = get_ficha_utilidades(fecha_inicio, fecha_fin)
  
    total_saldo_clientes        = sum(safe_to_float(item['total']) for item in valores_clientes)
    total_gastos_generales      = sum(safe_to_float(item['valor']) for item in valores_gastos)
    total_comisiones_proveedores = sum(safe_to_float(item['valor']) for item in fichas_proveedor)
    total_tarjetas = sum(item['valor'] for item in serializer.data if isinstance(item['valor'], (int, float)))
    
    
    #Nuevo total global de cargos no deseados
    total_cargo_no_deseados = (
        Cargosnodesados.objects
        .filter(id_cliente__isnull=True)  #sin cliente
        .aggregate(
            total_suma=Coalesce(
                Sum(
                    Cast(
                        Replace(
                            Replace(F('valor'), Value('.'), Value('')),
                            Value(','), Value('')
                        ),
                        output_field=models.BigIntegerField()
                    )
                ),
                0
            )
        )['total_suma'] or 0
    )

    recepcion_qs = RecepcionPago.objects.all()

    if fecha_inicio and fecha_fin:
        recepcion_qs = recepcion_qs.filter(fecha_transaccion__range=[fecha_inicio, fecha_fin])
    elif fecha_inicio:
        recepcion_qs = recepcion_qs.filter(fecha_transaccion__gte=fecha_inicio)
    elif fecha_fin:
        recepcion_qs = recepcion_qs.filter(fecha_transaccion__lte=fecha_fin)
    
    total_recepcion_pago = (
        recepcion_qs.aggregate(
            total_suma=Sum(
                Cast(
                    Replace(F("valor"), Value("."), Value("")),
                    output_field=models.IntegerField()
                )
            )
        )["total_suma"]
        or 0
    )

    # 🔢 Suma total de todos los valores
    suma_total = (
        total_saldo_clientes +
        total_gastos_generales +
        total_comisiones_proveedores +
        total_tarjetas + 
        total_cargo_no_deseados +
        total_recepcion_pago
    )

    # Construir arreglo estilo tarjetas
    clientes_info = {}
    for cliente in valores_clientes:
        nombre = cliente.get("nombre_cuenta") or f"Cargo no deseados {cliente.get('id', '')}"
        valor  = safe_to_float(cliente.get("total"))
        
        if nombre in clientes_info:
            clientes_info[nombre] += valor
        else:
            clientes_info[nombre] = valor

    # Convertir a lista como en tarjetas
    clientes_info = [
        {"nombre": nombre, "valor": valor}
        for nombre, valor in clientes_info.items()
        if valor != 0
    ]


    #print("suma_total ",suma_total)
    # ✅ Armar respuesta final uniendo ambos resultados
    respuesta_final = serializer.data + valores_clientes + valores_gastos + fichas_proveedor
    return Response({
        "datos": respuesta_final,
        "tarjetas": tarjetas_info,
        "clientes": clientes_info,
        "total_saldo_clientes": total_saldo_clientes,
        "total_gastos_generales": total_gastos_generales,
        "total_comisiones_proveedores": total_comisiones_proveedores,
        'totalTarjetas': total_tarjetas,
        "total_cargo_no_deseados": total_cargo_no_deseados,
        "total_recepcion_pago": total_recepcion_pago,
        "sumaTotal": suma_total,
        "utilidades":utilidades[0]['valor'],
        "total_cuatro_por_mil": obtener_datos_cuenta(fecha_inicio, fecha_fin)
    }, status=status.HTTP_200_OK)


"""
================================
======= PATRIMONIO BRUTO =======
================================
"""
def sumar_valores(queryset, campo="valor"):
    """
    Suma un campo numérico (como 'valor' o 'cuatro_por_mil') convirtiendo strings con puntos.
    """
    return queryset.aggregate(
        total_suma=Sum(
            Cast(
                Replace(F(campo), Value('.'), Value('')),
                output_field=models.BigIntegerField()
            )
        )
    )['total_suma'] or 0


def calcular_total_tarjetas():
    """
    Calcula el total general de todas las tarjetas (sumando valores de modelos asociados).
    Retorna el total de tarjetas y un diccionario con detalle por cada tarjeta.
    """
    total_tarjetas = Decimal(0)
    detalle = []

    cuentas = RegistroTarjetas.objects.all()
    serializer = RegistroTarjetasSerializer(cuentas, many=True)

    for cuenta in serializer.data:
        tarjeta_id = cuenta['id']

        rtaCuentaBancaria = sumar_valores(CuentaBancaria.objects.filter(idBanco=tarjeta_id), "valor")
        rtaRecepcionPago = sumar_valores(RecepcionPago.objects.filter(id_tarjeta_bancaria=tarjeta_id), "valor")
        rtaDevoluciones = sumar_valores(Devoluciones.objects.filter(id_tarjeta_bancaria=tarjeta_id), "valor")
        rtaCargosNoDeseados = sumar_valores(Cargosnodesados.objects.filter(id_tarjeta_bancaria=tarjeta_id), "valor")
        rtaGastogenerales = sumar_valores(Gastogenerales.objects.filter(id_tarjeta_bancaria=tarjeta_id), "valor")
        rtaUtilidadocacional = sumar_valores(Utilidadocacional.objects.filter(id_tarjeta_bancaria=tarjeta_id), "valor")

        total_general = (
            rtaCuentaBancaria +
            rtaRecepcionPago +
            rtaDevoluciones +
            rtaCargosNoDeseados +
            rtaGastogenerales +
            rtaUtilidadocacional
        )

        total_tarjetas += Decimal(total_general)

        detalle.append({
            "tarjeta_id": tarjeta_id,
            "total_tarjeta": total_general
        })

    return total_tarjetas, detalle


def calcular_total_cuatro_por_mil(detalle_tarjetas):
    """
    Calcula el total de cuatro por mil (4x1000) sumando por cada tarjeta y modelo relacionado.
    """
    total_cuatro_por_mil = Decimal(0)

    for item in detalle_tarjetas:
        tarjeta_id = item["tarjeta_id"]

        cuatro_por_mil_cuentas = sumar_valores(CuentaBancaria.objects.filter(idBanco=tarjeta_id), "cuatro_por_mil")
        cuatro_por_mil_recepciones = sumar_valores(RecepcionPago.objects.filter(id_tarjeta_bancaria=tarjeta_id), "cuatro_por_mil")
        cuatro_por_mil_devoluciones = sumar_valores(Devoluciones.objects.filter(id_tarjeta_bancaria=tarjeta_id), "cuatro_por_mil")
        cuatro_por_mil_gastos = sumar_valores(Gastogenerales.objects.filter(id_tarjeta_bancaria=tarjeta_id), "cuatro_por_mil")
        cuatro_por_mil_utilidad = sumar_valores(Utilidadocacional.objects.filter(id_tarjeta_bancaria=tarjeta_id), "cuatro_por_mil")

        total_por_tarjeta = abs(
            cuatro_por_mil_cuentas +
            cuatro_por_mil_recepciones +
            cuatro_por_mil_devoluciones +
            cuatro_por_mil_gastos +
            cuatro_por_mil_utilidad
        )

        total_cuatro_por_mil += Decimal(total_por_tarjeta)

    return total_cuatro_por_mil

# ==============================================================
# 💰 FUNCIÓN PRINCIPAL - OBTENER PATRIMONIO BRUTO
# ==============================================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1, 2)
def obtener_patrimonio_bruto(request):
    """
    Calcula el Patrimonio Bruto:
    Patrimonio Bruto = total_tarjetas - total_cuatro_por_mil - total_saldo_clientes
    """

    fecha_inicio = None
    fecha_fin = None

    try:
        if fecha_inicio:
            fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        if fecha_fin:
            fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d")
    except ValueError:
        return Response(
            {"error": "Formato de fecha inválido. Use YYYY-MM-DD."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # ---- 1️⃣ Calcular totales de tarjetas ----
    total_tarjetas, detalle_tarjetas = calcular_total_tarjetas()

    # ---- 2️⃣ Calcular total cuatro por mil ----
    total_cuatro_por_mil = calcular_total_cuatro_por_mil(detalle_tarjetas)

    # ---- 3️⃣ Calcular totales de clientes ----
    valores_clientes = get_all_ficha_cliente(fecha_inicio, fecha_fin)
    total_saldo_clientes = Decimal(sum(safe_to_float(item['total']) for item in valores_clientes))

    # ---- 4️⃣ Calcular Patrimonio Bruto ----
    patrimonio_bruto = abs(total_tarjetas - total_cuatro_por_mil - abs(total_saldo_clientes))

    # ---- Logs de validación ----
    print("=========== 🏦 totalTarjetas:", total_tarjetas)
    print("=========== 💸 total_cuatro_por_mil:", total_cuatro_por_mil)
    print("=========== 👥 total_saldo_clientes:", total_saldo_clientes)
    print("=========== 🧾 patrimonioBruto FINAL:", patrimonio_bruto)

    # ---- Respuesta final ----
    return Response({
        "totalTarjetas": round(total_tarjetas, 2),
        "total_cuatro_por_mil": round(total_cuatro_por_mil, 2),
        "total_saldo_clientes": round(abs(total_saldo_clientes), 2),
        "patrimonioBruto": round(patrimonio_bruto, 2)
    }, status=status.HTTP_200_OK)

"""
================================
======= PATRIMONIO NETO =======
================================
"""    
def obtener_patrimonio_bruto_function():
    """
    Calcula el patrimonio bruto total sin requerir request.
    Patrimonio Bruto = total_tarjetas - total_cuatro_por_mil - total_saldo_clientes
    """
    # ---- 1️⃣ Totales tarjetas ----
    total_tarjetas, detalle_tarjetas = calcular_total_tarjetas()

    # ---- 2️⃣ Total cuatro por mil ----
    total_cuatro_por_mil = calcular_total_cuatro_por_mil(detalle_tarjetas)

    # ---- 3️⃣ Totales clientes ----
    valores_clientes = get_all_ficha_cliente(None, None)
    total_saldo_clientes = Decimal(sum(safe_to_float(item['total']) for item in valores_clientes))

    # ---- 4️⃣ Cálculo del Patrimonio Bruto ----
    patrimonio_bruto = total_tarjetas - total_cuatro_por_mil - abs(total_saldo_clientes)

    # ---- Logs de validación (opcional) ----
    print("=========== 🏦 totalTarjetas (func):", total_tarjetas)
    print("=========== 💸 total_cuatro_por_mil (func):", total_cuatro_por_mil)
    print("=========== 👥 total_saldo_clientes (func):", total_saldo_clientes)
    print("=========== 🧾 patrimonioBruto FINAL (func):", patrimonio_bruto)

    # ---- Retornar solo el valor total (como hacía la versión original) ----
    return abs(patrimonio_bruto)

def safe_sum(queryset, field_name):
    from decimal import Decimal
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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1,2)
def obtener_patrimonio_neto_endpoint(request):
    print("==== obtener_patrimonio_neto_endpoint ====")
    try:
        fecha_inicio = request.GET.get("fechaInicio") 
        fecha_fin    = request.GET.get("fechaFin")

        try:
            if fecha_inicio:
                fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
                fecha_inicio = fecha_inicio.replace(hour=0, minute=0, second=0)
            if fecha_fin:
                fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d")
                fecha_fin = fecha_fin.replace(hour=23, minute=59, second=59)
        except ValueError:
            return Response({"error": "Formato de fecha inválido. Use YYYY-MM-DD."}, status=400)


        # ---- Helper para convertir a Decimal ----
        def to_decimal(value):
            if value in [None, "", "None"]:
                return Decimal("0")
            try:
                return Decimal(str(value).replace(".", "").replace(",", ""))
            except:
                return Decimal("0")

        # ---- Helper para aplicar filtro de fechas ----
        def apply_date_filter(qs, field_name):
            if fecha_inicio and fecha_fin:
                return qs.filter(**{f"{field_name}__range": [fecha_inicio, fecha_fin]})
            elif fecha_inicio:
                return qs.filter(**{f"{field_name}__gte": fecha_inicio})
            elif fecha_fin:
                return qs.filter(**{f"{field_name}__lte": fecha_fin})
            return qs

        # ---- Gastos Generales ----
        gastos_qs = apply_date_filter(Gastogenerales.objects.all(), "fecha_transaccion")
        total_gastos = safe_sum(gastos_qs, "valor") or Decimal("0")

        # ---- Reunir todos los cuatro_por_mil ----
        cuentas           = apply_date_filter(CuentaBancaria.objects.all(),    "fechaTransaccion").values("cuatro_por_mil")
        recepcion         = apply_date_filter(RecepcionPago.objects.all(),     "fecha_transaccion").values("cuatro_por_mil")
        devoluciones      = apply_date_filter(Devoluciones.objects.all(),      "fecha_transaccion").values("cuatro_por_mil")
        cargosnodesados   = apply_date_filter(Cargosnodesados.objects.all(),   "fecha_transaccion").values("cuatro_por_mil")
        gastos            = apply_date_filter(Gastogenerales.objects.all(),    "fecha_transaccion").values("cuatro_por_mil")
        utilidadocacional = apply_date_filter(Utilidadocacional.objects.all(), "fecha_transaccion").values("cuatro_por_mil")

        union_result = (
            list(cuentas) +
            list(recepcion) +
            list(devoluciones) +
            list(cargosnodesados) +
            list(gastos) +
            list(utilidadocacional)
        )

        total_cuatro_por_mil = sum(
            -abs(to_decimal(item.get("cuatro_por_mil")))
            for item in union_result
            if str(item.get("cuatro_por_mil")).strip() not in ["", "0", "None", None]
        )

        # ---- Patrimonio bruto ----
        patrimonio_bruto = Decimal(obtener_patrimonio_bruto_function())

        # ---- Response ----
        response_data = {
            "total_gastos"         : total_gastos,
            "total_cuatro_por_mil" : total_cuatro_por_mil,
            "t"                    : patrimonio_bruto,
            "patrimonio_neto"      : patrimonio_bruto + total_gastos + total_cuatro_por_mil
        }

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
"""
================================
===== FIN PATRIMONIO NETO =====
================================
"""

"""
================================
======= UTILIDAD NOMINAL =======
================================
"""    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1, 2)
def get_total_utilidad_nominal(request):
    fecha_inicio = request.GET.get('fechaInicio')
    fecha_fin    = request.GET.get('fechaFin')
    proveedor_id = None
    search       = None

    try:
        if fecha_inicio:
            fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        if fecha_fin:
            fecha_fin    = datetime.strptime(fecha_fin, "%Y-%m-%d")
    except ValueError:
        return Response({"error": "Formato de fecha inválido. Use YYYY-MM-DD."}, status=400)

    proveedores_qs = FichaProveedor.objects.all()

    if proveedor_id:
        proveedores_qs = proveedores_qs.filter(idproveedor__id=proveedor_id)

    if fecha_inicio and fecha_fin:
        proveedores_qs = proveedores_qs.filter(fechaCreacion__range=[fecha_inicio, fecha_fin])

    def safe_abs(value):
        try:
            return abs(float(value))
        except (ValueError, TypeError):
            return 0.0

    total_sum = 0.0

    for ficha in proveedores_qs:
        total_val = safe_abs(int(str(ficha.idcotizador.comisionPrecioLey).replace('.', '')))
        total_sum += total_val

    return Response({ "total": round(total_sum * 1, 2)})
"""
================================
===== FIN UTILIDAD NOMINAL =====
================================
"""

"""
================================
======== UTILIDAD REAL =========
================================
"""
def calcular_patrimonio_neto(fecha_inicio=None, fecha_fin=None):
    try:
        # ---- Helper para convertir a Decimal ----
        def to_decimal(value):
            if value in [None, "", "None"]:
                return Decimal("0")
            try:
                return Decimal(str(value).replace(".", "").replace(",", ""))
            except:
                return Decimal("0")

        # ---- Helper para aplicar filtro de fechas ----
        def apply_date_filter(qs, field_name):
            if fecha_inicio and fecha_fin:
                return qs.filter(**{f"{field_name}__range": [fecha_inicio, fecha_fin]})
            elif fecha_inicio:
                return qs.filter(**{f"{field_name}__gte": fecha_inicio})
            elif fecha_fin:
                return qs.filter(**{f"{field_name}__lte": fecha_fin})
            return qs

        # ---- Gastos Generales ----
        gastos_qs = apply_date_filter(Gastogenerales.objects.all(), "fecha_transaccion")
        total_gastos = safe_sum(gastos_qs, "valor") or Decimal("0")

        # ---- Reunir todos los cuatro_por_mil ----
        cuentas           = apply_date_filter(CuentaBancaria.objects.all(), "fechaTransaccion").values("cuatro_por_mil")
        recepcion         = apply_date_filter(RecepcionPago.objects.all(), "fecha_transaccion").values("cuatro_por_mil")
        devoluciones      = apply_date_filter(Devoluciones.objects.all(), "fecha_transaccion").values("cuatro_por_mil")
        cargosnodesados   = apply_date_filter(Cargosnodesados.objects.all(), "fecha_transaccion").values("cuatro_por_mil")
        gastos            = apply_date_filter(Gastogenerales.objects.all(), "fecha_transaccion").values("cuatro_por_mil")
        utilidadocacional = apply_date_filter(Utilidadocacional.objects.all(), "fecha_transaccion").values("cuatro_por_mil")

        union_result = (
            list(cuentas) +
            list(recepcion) +
            list(devoluciones) +
            list(cargosnodesados) +
            list(gastos) +
            list(utilidadocacional)
        )

        total_cuatro_por_mil = sum(
            -abs(to_decimal(item.get("cuatro_por_mil")))
            for item in union_result
            if str(item.get("cuatro_por_mil")).strip() not in ["", "0", "None", None]
        )

        # ---- Patrimonio neto ----
        patrimonio_bruto = Decimal(obtener_patrimonio_bruto_function())
        patrimonio_neto  = patrimonio_bruto + total_gastos + total_cuatro_por_mil

        return patrimonio_neto

    except Exception as e:
        raise Exception(f"Error al calcular patrimonio neto: {str(e)}")
    
def calcular_total_utilidad_nominal(fecha_inicio=None, fecha_fin=None, proveedor_id=None, search=None):
    try:
        # Convertir fechas SOLO si son str
        if isinstance(fecha_inicio, str):
            fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        if isinstance(fecha_fin, str):
            fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d")
    except ValueError:
        raise Exception("Formato de fecha inválido. Use YYYY-MM-DD.")

    proveedores_qs = FichaProveedor.objects.all()

    if proveedor_id:
        proveedores_qs = proveedores_qs.filter(idproveedor__id=proveedor_id)

    if fecha_inicio and fecha_fin:
        proveedores_qs = proveedores_qs.filter(fechaCreacion__range=[fecha_inicio, fecha_fin])

    if search:
        proveedores_qs = proveedores_qs.filter(
            Q(id__icontains=search) |
            Q(idproveedor__nombre__icontains=search) |
            Q(comisionproveedor__icontains=search) |
            Q(idcotizador__etiquetaDos__icontains=search) |
            Q(idcotizador__placa__icontains=search) |
            Q(idcotizador__cilindraje__icontains=search) |
            Q(idcotizador__modelo__icontains=search) |
            Q(idcotizador__chasis__icontains=search) |
            Q(idcotizador__precioDeLey__icontains=search) |
            Q(idcotizador__comisionPrecioLey__icontains=search) |
            Q(idcotizador__total__icontains=search)
        )

    def safe_abs(value):
        try:
            return abs(float(value))
        except (ValueError, TypeError):
            return 0.0

    total_sum = 0.0
    for ficha in proveedores_qs:
        total_val = safe_abs(int(str(ficha.idcotizador.comisionPrecioLey).replace('.', '')))
        total_sum += total_val

    return Decimal(str(round(total_sum * -1)))

def obtener_patrimonio_neto(fecha_inicio=None, fecha_fin=None):
    try:
        # ---- Helper para convertir a Decimal ----
        def to_decimal(value):
            if value in [None, "", "None"]:
                return Decimal("0")
            try:
                return Decimal(str(value).replace(".", "").replace(",", ""))
            except:
                return Decimal("0")

        # ---- Helper para aplicar filtro de fechas ----
        def apply_date_filter(qs, field_name):
            if fecha_inicio and fecha_fin:
                return qs.filter(**{f"{field_name}__range": [fecha_inicio, fecha_fin]})
            elif fecha_inicio:
                return qs.filter(**{f"{field_name}__gte": fecha_inicio})
            elif fecha_fin:
                return qs.filter(**{f"{field_name}__lte": fecha_fin})
            return qs

        # ---- Gastos Generales ----
        gastos_qs = apply_date_filter(Gastogenerales.objects.all(), "fecha_transaccion")
        total_gastos = safe_sum(gastos_qs, "valor") or Decimal("0")

        # ---- Reunir todos los cuatro_por_mil ----
        cuentas           = apply_date_filter(CuentaBancaria.objects.all(),    "fechaTransaccion").values("cuatro_por_mil")
        recepcion         = apply_date_filter(RecepcionPago.objects.all(),     "fecha_transaccion").values("cuatro_por_mil")
        devoluciones      = apply_date_filter(Devoluciones.objects.all(),      "fecha_transaccion").values("cuatro_por_mil")
        cargosnodesados   = apply_date_filter(Cargosnodesados.objects.all(),   "fecha_transaccion").values("cuatro_por_mil")
        gastos            = apply_date_filter(Gastogenerales.objects.all(),    "fecha_transaccion").values("cuatro_por_mil")
        utilidadocacional = apply_date_filter(Utilidadocacional.objects.all(), "fecha_transaccion").values("cuatro_por_mil")

        union_result = (
            list(cuentas) +
            list(recepcion) +
            list(devoluciones) +
            list(cargosnodesados) +
            list(gastos) +
            list(utilidadocacional)
        )

        total_cuatro_por_mil = sum(
            -abs(to_decimal(item.get("cuatro_por_mil")))
            for item in union_result
            if str(item.get("cuatro_por_mil")).strip() not in ["", "0", "None", None]
        )

        # ---- Patrimonio bruto ----
        patrimonio_bruto = Decimal(obtener_patrimonio_bruto_function())

        # ---- Patrimonio neto ----
        patrimonio_neto = patrimonio_bruto + total_gastos + total_cuatro_por_mil

        return patrimonio_neto

    except Exception as e:
        raise Exception(f"Error al calcular patrimonio neto: {str(e)}")
    
def calcular_gastos_totales(fecha_inicio=None, fecha_fin=None):
    """
    Calcula el total de gastos generales en el periodo dado.
    Si no se pasan fechas, trae todos los registros.
    """

    # ---- Helper para convertir a Decimal ----
    def to_decimal(value):
        if value in [None, "", "None"]:
            return Decimal("0")
        try:
            return Decimal(str(value).replace(".", "").replace(",", ""))
        except:
            return Decimal("0")

    # ---- Helper para aplicar filtro de fechas ----
    def apply_date_filter(qs, field_name):
        if fecha_inicio and fecha_fin:
            return qs.filter(**{f"{field_name}__range": [fecha_inicio, fecha_fin]})
        elif fecha_inicio:
            return qs.filter(**{f"{field_name}__gte": fecha_inicio})
        elif fecha_fin:
            return qs.filter(**{f"{field_name}__lte": fecha_fin})
        return qs

    # ---- Gastos Generales ----
    gastos_qs = apply_date_filter(Gastogenerales.objects.all(), "fecha_transaccion")

    total_gastos = safe_sum(gastos_qs, "valor") or Decimal("0")

    return total_gastos

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1, 2)
def total_utilidad_real(request):
    fecha_inicio = request.GET.get('fechaInicio')
    fecha_fin    = request.GET.get('fechaFin')

    try:
        if fecha_inicio:
            fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        if fecha_fin:
            fecha_fin    = datetime.strptime(fecha_fin, "%Y-%m-%d")
    except ValueError:
        return Response({"error": "Formato de fecha inválido. Use YYYY-MM-DD."}, status=400)
 
    try:
        calcular_gastos     = gasto_totales_del_periodo_real(fecha_inicio, fecha_fin) #calcular_gastos_totales(fecha_inicio, fecha_fin) #calcular_patrimonio_neto()
        utilidad_nominal    = Decimal(calcular_total_utilidad_nominal(fecha_inicio, fecha_fin))
        
        total_utilidad_real = abs(utilidad_nominal)
        total = total_utilidad_real - calcular_gastos
       
        return Response({
            "calcular_gastos_totales"         : round(calcular_gastos),
            "utilidad_nominal"                : round(abs(utilidad_nominal)),
            "total_utilidad_real"             : round(total),
            "resultado"                       : round(total),
        })

    except Exception as e:
        return Response({"error": str(e)}, status=500)

"""
================================
======= FIN UTILIDAD REAL ======
================================
"""

"""
================================
===== UTILIDAD DIFERENCIAL =====
================================
"""
def total_diferencial_utilidad_real(fecha_inicio=None, fecha_fin=None):
    try:
        if fecha_inicio:
            fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        if fecha_fin:
            fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Formato de fecha inválido. Use YYYY-MM-DD.")

    try:
        patrimonio = obtener_patrimonio_neto()
        resultado = Decimal(calcular_total_utilidad_nominal(fecha_inicio, fecha_fin))

        # ✅ Siempre restar el resultado en valor absoluto
        total_utilidad_real = patrimonio - abs(resultado)

        return round(total_utilidad_real)

    except Exception as e:
        raise Exception(f"Error calculando utilidad real: {str(e)}")
    

def total_diferencial_utilidad_nominal(fecha_inicio=None, fecha_fin=None, proveedor_id=None, search=None):
    """
    Calcula la utilidad nominal total en base a los filtros aplicados.
    Retorna solo un valor numérico (float).
    """

    # Validar fechas
    try:
        if fecha_inicio:
            fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        if fecha_fin:
            fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Formato de fecha inválido. Use YYYY-MM-DD.")

    proveedores_qs = FichaProveedor.objects.all()

    if proveedor_id:
        proveedores_qs = proveedores_qs.filter(idproveedor__id=proveedor_id)

    if fecha_inicio and fecha_fin:
        proveedores_qs = proveedores_qs.filter(fechaCreacion__range=[fecha_inicio, fecha_fin])

    if search:
        proveedores_qs = proveedores_qs.filter(
            Q(id__icontains=search) |
            Q(idproveedor__nombre__icontains=search) |
            Q(comisionproveedor__icontains=search) |
            Q(idcotizador__etiquetaDos__icontains=search) |
            Q(idcotizador__placa__icontains=search) |
            Q(idcotizador__cilindraje__icontains=search) |
            Q(idcotizador__modelo__icontains=search) |
            Q(idcotizador__chasis__icontains=search) |
            Q(idcotizador__precioDeLey__icontains=search) |
            Q(idcotizador__comisionPrecioLey__icontains=search) |
            Q(idcotizador__total__icontains=search)
        )

    def safe_abs(value):
        try:
            return abs(float(value))
        except (ValueError, TypeError):
            return 0.0

    total_sum = 0.0

    for ficha in proveedores_qs:
        total_val = safe_abs(int(str(ficha.idcotizador.comisionPrecioLey).replace('.', '')))
        total_sum += total_val

    return round(total_sum)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1, 2)
def total_diferencia(request):
    fecha_inicio = request.GET.get('fechaInicio')
    fecha_fin    = request.GET.get('fechaFin')

    try:
        if fecha_inicio:
            fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        if fecha_fin:
            fecha_fin    = datetime.strptime(fecha_fin, "%Y-%m-%d")
    except ValueError:
        return Response({"error": "Formato de fecha inválido. Use YYYY-MM-DD."}, status=400)

    try:
        real        = total_diferencial_utilidad_real()
        nominal     = total_diferencial_utilidad_nominal()
        total_diferencia = float(real) - float(nominal)

        return Response({
            "total_diferencia"  : round(total_diferencia),
            "real"              : round(real),
            "nominal"           : round(nominal)
        })

    except Exception as e:
        return Response({"error": str(e)}, status=500)

"""
================================
=== FIN UTILIDAD DIFERENCIAL ===
================================
"""

"""
================================
=== GASTOS TOTALES DEL PERIODO ===
================================
"""
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1, 2)
def gasto_totales_del_periodo(request):
    try:
        fecha_inicio = request.GET.get("fechaInicio") 
        fecha_fin    = request.GET.get("fechaFin")

        # ---- Helper para convertir a Decimal ----
        def to_decimal(value):
            if value in [None, "", "None"]:
                return Decimal("0")
            try:
                return Decimal(str(value).replace(".", "").replace(",", ""))
            except:
                return Decimal("0")

        # ---- Helper para aplicar filtro de fechas ----
        def apply_date_filter(qs, field_name):
            if fecha_inicio and fecha_fin:
                return qs.filter(**{f"{field_name}__range": [fecha_inicio, fecha_fin]})
            elif fecha_inicio:
                return qs.filter(**{f"{field_name}__gte": fecha_inicio})
            elif fecha_fin:
                return qs.filter(**{f"{field_name}__lte": fecha_fin})
            return qs

        # ---- Gastos Generales ----
        gastos_qs    = apply_date_filter(Gastogenerales.objects.all(), "fecha_transaccion")
        total_gastos = safe_sum(gastos_qs, "valor") or Decimal("0")

        # ---- Reunir todos los cuatro_por_mil ----
        cuentas           = apply_date_filter(CuentaBancaria.objects.all(),    "fechaTransaccion").values("cuatro_por_mil")
        recepcion         = apply_date_filter(RecepcionPago.objects.all(),     "fecha_transaccion").values("cuatro_por_mil")
        devoluciones      = apply_date_filter(Devoluciones.objects.all(),      "fecha_transaccion").values("cuatro_por_mil")
        cargosnodesados   = apply_date_filter(Cargosnodesados.objects.all(),   "fecha_transaccion").values("cuatro_por_mil")
        gastos            = apply_date_filter(Gastogenerales.objects.all(),    "fecha_transaccion").values("cuatro_por_mil")
        utilidadocacional = apply_date_filter(Utilidadocacional.objects.all(), "fecha_transaccion").values("cuatro_por_mil")

        union_result = (
            list(cuentas) +
            list(recepcion) +
            list(devoluciones) +
            list(cargosnodesados) +
            list(gastos) +
            list(utilidadocacional)
        )

        total_cuatro_por_mil = sum(
            abs(to_decimal(item.get("cuatro_por_mil")))
            for item in union_result
            if str(item.get("cuatro_por_mil")).strip() not in ["", "0", "None", None]
        )

        # ---- Response ----
        response_data = {
            "total_gastos"              : total_gastos,
            "total_cuatro_por_mil"      : total_cuatro_por_mil,
            "gastos_totales_de_periodo" : total_cuatro_por_mil - total_gastos
        }

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

def gasto_totales_del_periodo_real(fecha_inicio, fecha_fin):
    try:
        fecha_inicio = fecha_inicio 
        fecha_fin    = fecha_fin

        # ---- Helper para convertir a Decimal ----
        def to_decimal(value):
            if value in [None, "", "None"]:
                return Decimal("0")
            try:
                return Decimal(str(value).replace(".", "").replace(",", ""))
            except:
                return Decimal("0")

        # ---- Helper para aplicar filtro de fechas ----
        def apply_date_filter(qs, field_name):
            if fecha_inicio and fecha_fin:
                return qs.filter(**{f"{field_name}__range": [fecha_inicio, fecha_fin]})
            elif fecha_inicio:
                return qs.filter(**{f"{field_name}__gte": fecha_inicio})
            elif fecha_fin:
                return qs.filter(**{f"{field_name}__lte": fecha_fin})
            return qs

        # ---- Gastos Generales ----
        gastos_qs    = apply_date_filter(Gastogenerales.objects.all(), "fecha_transaccion")
        total_gastos = safe_sum(gastos_qs, "valor") or Decimal("0")

        # ---- Reunir todos los cuatro_por_mil ----
        cuentas           = apply_date_filter(CuentaBancaria.objects.all(),    "fechaTransaccion").values("cuatro_por_mil")
        recepcion         = apply_date_filter(RecepcionPago.objects.all(),     "fecha_transaccion").values("cuatro_por_mil")
        devoluciones      = apply_date_filter(Devoluciones.objects.all(),      "fecha_transaccion").values("cuatro_por_mil")
        cargosnodesados   = apply_date_filter(Cargosnodesados.objects.all(),   "fecha_transaccion").values("cuatro_por_mil")
        gastos            = apply_date_filter(Gastogenerales.objects.all(),    "fecha_transaccion").values("cuatro_por_mil")
        utilidadocacional = apply_date_filter(Utilidadocacional.objects.all(), "fecha_transaccion").values("cuatro_por_mil")

        union_result = (
            list(cuentas) +
            list(recepcion) +
            list(devoluciones) +
            list(cargosnodesados) +
            list(gastos) +
            list(utilidadocacional)
        )

        total_cuatro_por_mil = sum(
            abs(to_decimal(item.get("cuatro_por_mil")))
            for item in union_result
            if str(item.get("cuatro_por_mil")).strip() not in ["", "0", "None", None]
        )

        # ---- Response ----
        response_data = {
            "total_gastos"              : total_gastos,
            "total_cuatro_por_mil"      : total_cuatro_por_mil,
            "gastos_totales_de_periodo" : total_cuatro_por_mil - total_gastos
        }

        return total_cuatro_por_mil - total_gastos

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
"""
================================
=== END GASTOS TOTALES DEL PERIODO ===
================================
"""