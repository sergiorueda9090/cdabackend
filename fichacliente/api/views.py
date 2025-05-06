from rest_framework.decorators import api_view, permission_classes
from rest_framework.response   import Response

from cuentasbancarias.models    import CuentaBancaria
from cotizador.models           import Cotizador
from clientes.models            import Cliente
from recepcionPago.models       import RecepcionPago
from devoluciones.models        import Devoluciones
from ajustesaldos.models        import Ajustesaldo
from django.db.models           import F, Value, CharField, Sum, Q
from datetime import datetime
from rest_framework.permissions import IsAuthenticated
from users.decorators import check_role

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1, 2)
def get_all_ficha_cliente(request):
    # Obtener parámetros de fecha
    fecha_inicio = request.GET.get('fechaInicio')
    fecha_fin = request.GET.get('fechaFin')

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

    return Response(union_result)