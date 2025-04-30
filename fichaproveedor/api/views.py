from rest_framework.decorators  import api_view, permission_classes
from django.db.models           import Q
from rest_framework.response    import Response
from rest_framework             import status
from cuentasbancarias.models    import CuentaBancaria
from cotizador.models           import Cotizador
from clientes.models            import Cliente
from recepcionPago.models       import RecepcionPago
from devoluciones.models        import Devoluciones
from ajustesaldos.models        import Ajustesaldo

from proveedores.models         import Proveedor
from fichaproveedor.models      import FichaProveedor

from django.db.models           import F, Value, CharField, Sum, Q, FloatField
from django.db.models.functions import Cast, Coalesce
from datetime import datetime
from rest_framework.permissions import IsAuthenticated

from .serializers import FichaProveedorSerializer

from users.decorators import check_role

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1,2)
def get_all_fecha_proveedores(request):
    # Obtener parámetros de fecha
    fecha_inicio = request.GET.get('fechaInicio')
    fecha_fin    = request.GET.get('fechaFin')

    # Validar formato de fecha
    try:
        if fecha_inicio:
            fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        if fecha_fin:
            fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d")
    except ValueError:
        return Response({"error": "Formato de fecha inválido. Use YYYY-MM-DD."}, status=400)

    # Obtener proveedores con filtro opcional por fecha
    proveedores_qs = FichaProveedor.objects.all()
    
    if fecha_inicio and fecha_fin:
        proveedores_qs = proveedores_qs.filter(fechaCreacion__range=[fecha_inicio, fecha_fin])

        # Transformar los datos en la estructura deseada
    data = [
        {
            "id"                : ficha.id,
            "nombre"            : ficha.idproveedor.nombre,
            "comisionproveedor" : ficha.comisionproveedor,
            "etiquetaDos"       : ficha.idcotizador.etiquetaDos,
            "placa"             : ficha.idcotizador.placa,
            "cilindraje"        : ficha.idcotizador.cilindraje,
            "modelo"            : ficha.idcotizador.modelo,
            "chasis"            : ficha.idcotizador.chasis,
            "precioDeLey"       : ficha.idcotizador.precioDeLey,
            "comisionPrecioLey" : ficha.idcotizador.comisionPrecioLey,
            "total"             : ficha.idcotizador.total,
        }
        for ficha in proveedores_qs
    ]

    return Response(data)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1,2)
def get_all_ficha_test(request):
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
    cotizadores_qs = Cotizador.objects.exclude(precioDeLey__isnull=True).exclude(precioDeLey="").values('id', 'fechaCreacion', 'total', 'idCliente', 'placa', 'archivo')
   
    # Aplicar filtro por fecha si es necesario
    if fecha_inicio and fecha_fin:
        cotizadores_qs = cotizadores_qs.filter(fechaCreacion__range=[fecha_inicio, fecha_fin])


    # 2. Obtener los clientes en un diccionario {id: nombre}
    clientes_dict = {c['id']: c['nombre'] for c in Cliente.objects.values('id', 'nombre')}

    #valor total
    cuentasbancarias_qs = {c['idCotizador']: c['valor'] for c in CuentaBancaria.objects.values('idCotizador', 'valor')}
    
    # 3. Formatear cotizadores en una lista
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
        if cuentasbancarias_qs.get(cotizador['id'], "Desconocido") != "Desconocido"
        and clientes_dict.get(cotizador['idCliente'], "Desconocido") != "Desconocido"
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
            origen = Value("Recepcion de Pago", output_field=CharField()),
            placa = Value("", output_field=CharField()),
            archivo = Value("", output_field=CharField()),
        ).values('id', 'fi', 'ft', 'valor_alias', 'desc_alias', 'cliente_nombre', "origen", "placa", "archivo"))
    
    devoluciones = list(Devoluciones.objects.select_related('id_cliente')
        .filter(filtros_fecha)
        .annotate(
            fi = F('fecha_ingreso'),
            ft = F('fecha_transaccion'),
            valor_alias = F('valor'),
            desc_alias = F('observacion'),
            cliente_nombre = F('id_cliente__nombre'),
            origen = Value("Devoluciones", output_field=CharField()),
            placa = Value("", output_field=CharField()),
            archivo = Value("", output_field=CharField()),
        ).values('id', 'fi', 'ft', 'valor_alias', 'desc_alias', 'cliente_nombre', "origen", "placa", "archivo"))

    ajuestesSaldos = list(Ajustesaldo.objects.select_related('id_cliente')
        .filter(filtros_fecha)
        .annotate(
            fi = F('fecha_ingreso'),
            ft = F('fecha_transaccion'),
            valor_alias = F('valor'),
            desc_alias = F('observacion'),
            cliente_nombre = F('id_cliente__nombre'),
            origen = Value("Ajustes de Saldos", output_field=CharField()),
            placa = Value("", output_field=CharField()),
            archivo = Value("", output_field=CharField()),
        ).values('id', 'fi', 'ft', 'valor_alias', 'desc_alias', 'cliente_nombre', "origen", "placa", "archivo"))

    # 5. Unir todos los resultados
    union_result = cotizadores_list + recepcionDePagos + devoluciones + ajuestesSaldos

    return Response(union_result)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1,2)
def get_ficha_proveedores(request):
    fecha_inicio = request.GET.get('fechaInicio')
    fecha_fin    = request.GET.get('fechaFin')

    try:
        if fecha_inicio:
            fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        if fecha_fin:
            fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d")
    except ValueError:
        return Response({"error": "Formato de fecha inválido. Use YYYY-MM-DD."}, status=400)

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

    data = [
        {
            'id': item['idproveedor__id'],
            'nombre': item['idproveedor__nombre'],
            'etiqueta': item['idcotizador__etiquetaDos'],
            'comision_total': item['total_comision']
        }
        for item in agrupado
    ]

    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1,2)
def get_ficha_proveedor_por_id(request):
    fecha_inicio = request.GET.get('fechaInicio')
    fecha_fin    = request.GET.get('fechaFin')
    proveedor_id = request.GET.get('proveedorId')
    search       = request.GET.get('search')  # <-- nuevo parámetro

    try:
        if fecha_inicio:
            fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
        if fecha_fin:
            fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d")
    except ValueError:
        return Response({"error": "Formato de fecha inválido. Use YYYY-MM-DD."}, status=400)

    proveedores_qs = FichaProveedor.objects.all()

    if proveedor_id:
        proveedores_qs = proveedores_qs.filter(idproveedor__id=proveedor_id)

    if fecha_inicio and fecha_fin:
        proveedores_qs = proveedores_qs.filter(fechaCreacion__range=[fecha_inicio, fecha_fin])
    else:
        # Si NO mandan fechas, mostrar solo registros del día de hoy
        hoy = datetime.now().date()
        proveedores_qs = proveedores_qs.filter(fechaCreacion__date=hoy)

    # Si viene el parámetro "search", aplicar filtro
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

    data = [
        {
            "id"                : ficha.id,
            "nombre"            : ficha.idproveedor.nombre,
            "comisionproveedor" : ficha.comisionproveedor,
            "etiquetaDos"       : ficha.idcotizador.etiquetaDos,
            "placa"             : ficha.idcotizador.placa,
            "cilindraje"        : ficha.idcotizador.cilindraje,
            "modelo"            : ficha.idcotizador.modelo,
            "chasis"            : ficha.idcotizador.chasis,
            "precioDeLey"       : ficha.idcotizador.precioDeLey,
            "comisionPrecioLey" : ficha.idcotizador.comisionPrecioLey,
            "total"             : ficha.idcotizador.total,
        }
        for ficha in proveedores_qs
    ]

    return Response(data)