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

from fichaproveedor.api.serializers import FichaProveedorSerializer

from users.decorators import check_role

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1, 2)
def get_ficha_utilidades(request):
    fecha_inicio = request.GET.get('fechaInicio')
    fecha_fin    = request.GET.get('fechaFin')
    proveedor_id = request.GET.get('proveedorId')
    search       = request.GET.get('search')

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
    #else:
    #    hoy = datetime.now().date()
    #    proveedores_qs = proveedores_qs.filter(fechaCreacion__date=hoy)

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

    data = []
    total_sum = 0.0

    for ficha in proveedores_qs:
        total_val = safe_abs(int(str(ficha.idcotizador.comisionPrecioLey).replace('.', '')))
        total_sum += total_val

        data.append({
            "id"                : ficha.id,
            "nombre"            : ficha.idproveedor.nombre,
            "comisionproveedor" : int(str(ficha.idcotizador.comisionPrecioLey).replace('.', '')),
            "etiquetaDos"       : ficha.idcotizador.etiquetaDos,
            "placa"             : ficha.idcotizador.placa,
            "cilindraje"        : ficha.idcotizador.cilindraje,
            "modelo"            : ficha.idcotizador.modelo,
            "chasis"            : ficha.idcotizador.chasis,
            "precioDeLey"       : safe_abs(ficha.idcotizador.precioDeLey),
            "comisionPrecioLey" : safe_abs(ficha.idcotizador.comisionPrecioLey),
            "total"             : total_val,
        })

    return Response({
        "data": data,
        "total": round(total_sum, 2)
    })