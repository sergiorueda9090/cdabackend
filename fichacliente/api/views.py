from rest_framework.decorators import api_view
from rest_framework.response   import Response

from cotizador.models           import Cotizador
from clientes.models            import Cliente
from recepcionPago.models       import RecepcionPago
from devoluciones.models        import Devoluciones
from ajustesaldos.models        import Ajustesaldo
from django.db.models           import F, Value, CharField, Sum, Q
from datetime import datetime

@api_view(['GET'])
def get_all_ficha_cliente(request):
    # Obtener parámetros de fecha
    fecha_inicio = request.GET.get('fechaInicio')
    fecha_fin = request.GET.get('fechaFin')
    # Convertir a objeto datetime si se proporcionan
    try:
        if fecha_inicio:
            fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        if fecha_fin:
            fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d")
    except ValueError:
        return Response({"error": "Formato de fecha inválido. Use YYYY-MM-DD."}, status=400)

    # 1. Obtener los cotizadores con sus idCliente
    cotizadores_qs = Cotizador.objects.values('id', 'fechaCreacion', 'total', 'idCliente')

    # Aplicar filtro por fecha si es necesario
    if fecha_inicio and fecha_fin:
        cotizadores_qs = cotizadores_qs.filter(fechaCreacion__range=[fecha_inicio, fecha_fin])

    # 2. Obtener los clientes en un diccionario {id: nombre}
    clientes_dict = {c['id']: c['nombre'] for c in Cliente.objects.values('id', 'nombre')}

    # 3. Formatear cotizadores en una lista
    cotizadores_list = [
        {
            'id': cotizador['id'],
            'fi': cotizador['fechaCreacion'],
            'ft': None,
            'valor_alias': cotizador['total'],
            'desc_alias': "",
            'cliente_nombre': clientes_dict.get(cotizador['idCliente'], "Desconocido"),
            'origen': "Cotizador"
        }
        for cotizador in cotizadores_qs
    ]

    # 4. Obtener y filtrar los otros modelos
    filtros_fecha = Q()
    if fecha_inicio and fecha_fin:
        filtros_fecha = Q(fi__range=[fecha_inicio, fecha_fin])

    recepcionDePagos = list(RecepcionPago.objects.select_related('cliente')
        .filter(filtros_fecha)
        .annotate(
            fi = F('fecha_ingreso'),
            ft = F('fecha_transaccion'),
            valor_alias = F('valor'),
            desc_alias = F('observacion'),
            cliente_nombre = F('cliente__nombre'),
            origen = Value("Recepcion de Pago", output_field=CharField())
        ).values('id', 'fi', 'ft', 'valor_alias', 'desc_alias', 'cliente_nombre', "origen"))
    
    devoluciones = list(Devoluciones.objects.select_related('id_cliente')
        .filter(filtros_fecha)
        .annotate(
            fi = F('fecha_ingreso'),
            ft = F('fecha_transaccion'),
            valor_alias = F('valor'),
            desc_alias = F('observacion'),
            cliente_nombre = F('id_cliente__nombre'),
            origen = Value("Devoluciones", output_field=CharField())
        ).values('id', 'fi', 'ft', 'valor_alias', 'desc_alias', 'cliente_nombre', "origen"))

    ajuestesSaldos = list(Ajustesaldo.objects.select_related('id_cliente')
        .filter(filtros_fecha)
        .annotate(
            fi = F('fecha_ingreso'),
            ft = F('fecha_transaccion'),
            valor_alias = F('valor'),
            desc_alias = F('observacion'),
            cliente_nombre = F('id_cliente__nombre'),
            origen = Value("Ajustes de Saldos", output_field=CharField())
        ).values('id', 'fi', 'ft', 'valor_alias', 'desc_alias', 'cliente_nombre', "origen"))

    # 5. Unir todos los resultados
    union_result = cotizadores_list + recepcionDePagos + devoluciones + ajuestesSaldos

    return Response(union_result)