from rest_framework.decorators import api_view, permission_classes
from rest_framework.response   import Response
from decimal import Decimal
from rest_framework             import status
from cuentasbancarias.models    import CuentaBancaria
from cotizador.models           import Cotizador
from clientes.models            import Cliente
from recepcionPago.models       import RecepcionPago
from devoluciones.models        import Devoluciones
from ajustesaldos.models        import Ajustesaldo
from django.db.models           import F, Value, CharField, Sum, Q
from cargosnoregistrados.models import Cargosnodesados
from cotizador.api.serializers  import CotizadorSerializer
from datetime import datetime
from rest_framework.permissions import IsAuthenticated
from users.decorators import check_role
import uuid

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1, 2)
def get_all_ficha_cliente_agrupado(request):

    def safe_float(value):
        try:
            if value is None or value == "":
                return 0.0
            s = str(value).strip()
            if "." in s and "," in s:
                if s.rfind(".") > s.rfind(","):
                    s = s.replace(",", "")
                else:
                    s = s.replace(".", "").replace(",", ".")
            elif "," in s:
                s = s.replace(".", "").replace(",", ".")
            else:
                s = s.replace(",", "")
            return float(s)
        except:
            return 0.0

    def format_value(value):
        try:
            valor = safe_float(value)
            signo = "-" if valor < 0 else ""
            valor_str = f"{int(abs(valor)):,}".replace(",", ".")
            return f"{signo}{valor_str}"
        except:
            return value

    def parse_fecha(fecha_str):
        if not fecha_str:
            return datetime.min
        if isinstance(fecha_str, datetime):
            return fecha_str
        for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
            try:
                return datetime.strptime(str(fecha_str)[:19], fmt)
            except:
                pass
        return datetime.min


    # ===============================================
    # ⭐ MAP DATA CON CAMPOS NUEVOS (Placa, Cilindraje, Año)
    # ===============================================
    def map_data(lista, tipo, origen, field_valor='valor', field_obs='observacion',
                 negativo=False, es_soat=False):
        data = []
        for item in lista:
            valor = safe_float(item.get(field_valor))
            if negativo:
                valor *= -1

            fecha_ingreso = item.get('fecha_ingreso')
            fecha_transaccion = item.get('fecha_transaccion')

            # CAMPOS EXTRAS SOLO PARA SOAT
            placa = item.get("placa", "") if es_soat else ""
            cilindraje = item.get("cilindraje", "") if es_soat else ""
            anio = item.get("modelo", "") if es_soat else ""

            data.append({
                "id": str(uuid.uuid4()),
                "valor": format_value(valor),
                "tipo": tipo,
                "origen": f"Cliente - {origen}",
                "observacion": item.get(field_obs, "") or "",
                "placa": placa,
                "cilindraje": cilindraje,
                "anio": anio,
                "fecha_ingreso": fecha_ingreso,
                "fecha_transaccion": fecha_transaccion,
                "fecha": fecha_ingreso or fecha_transaccion,
            })
        return data


    clientes_data = {}

    # =======================
    # ⭐ COTIZADORES (SOAT)
    # =======================
    cotizadores = (
        Cotizador.objects
        .annotate(
            fecha_ingreso=F('fechaCreacion'),
            fecha_transaccion=F('fechaTramite')
        )
        .values(
            'id', 'idCliente', 'precioDeLey', 'total',
            'placa', 'cilindraje', 'modelo',
            'fecha_ingreso', 'fecha_transaccion'
        )
    )

    for c in cotizadores:
        cliente = Cliente.objects.filter(id=c["idCliente"]).first()
        if not cliente:
            continue

        cid = cliente.id

        if cid not in clientes_data:
            clientes_data[cid] = {
                "cliente": cliente.nombre,
                "total": 0,
                "movimientos": [],
                "cotizador": []
            }

        movs = map_data(
            [c],
            "SOAT",
            "Trámites",
            field_valor="total",
            field_obs="",
            negativo=True,
            es_soat=True
        )
        clientes_data[cid]["movimientos"] += movs
        clientes_data[cid]["total"] -= safe_float(c["total"])

        cot = Cotizador.objects.get(id=c["id"])
        ser = CotizadorSerializer(cot).data
        ser["nombre_cliente"] = cliente.nombre
        clientes_data[cid]["cotizador"].append(ser)

    # =======================
    # RECEPCIÓN PAGO
    # =======================
    recepciones = RecepcionPago.objects.values(
        'id', 'cliente_id', 'valor', 'observacion',
        'fecha_ingreso', 'fecha_transaccion'
    )

    for r in recepciones:
        cliente = Cliente.objects.filter(id=r["cliente_id"]).first()
        if not cliente:
            continue

        cid = cliente.id

        if cid not in clientes_data:
            clientes_data[cid] = {
                "cliente": cliente.nombre,
                "total": 0,
                "movimientos": [],
                "cotizador": []
            }

        movs = map_data([r], "Recepción de pago", "Recepción de Pago")
        clientes_data[cid]["movimientos"] += movs
        clientes_data[cid]["total"] += safe_float(r["valor"])

    # =======================
    # AJUSTES
    # =======================
    ajustes = Ajustesaldo.objects.values(
        'id', 'id_cliente', 'valor', 'observacion',
        'fecha_ingreso', 'fecha_transaccion'
    )

    for a in ajustes:
        cliente = Cliente.objects.filter(id=a["id_cliente"]).first()
        if not cliente:
            continue

        cid = cliente.id

        if cid not in clientes_data:
            clientes_data[cid] = {
                "cliente": cliente.nombre,
                "total": 0,
                "movimientos": [],
                "cotizador": []
            }

        movs = map_data([a], "Ajuste de saldo", "Ajustes de Saldos")
        clientes_data[cid]["movimientos"] += movs
        clientes_data[cid]["total"] += safe_float(a["valor"])


    # =======================
    # DEVOLUCIONES
    # =======================
    devoluciones = Devoluciones.objects.values(
        'id', 'id_cliente', 'valor', 'observacion',
        'fecha_ingreso', 'fecha_transaccion'
    )

    for d in devoluciones:
        cliente = Cliente.objects.filter(id=d["id_cliente"]).first()
        if not cliente:
            continue

        cid = cliente.id

        if cid not in clientes_data:
            clientes_data[cid] = {
                "cliente": cliente.nombre,
                "total": 0,
                "movimientos": [],
                "cotizador": []
            }

        movs = map_data([d], "Devolución", "Devoluciones")
        clientes_data[cid]["movimientos"] += movs
        clientes_data[cid]["total"] += safe_float(d["valor"])

    # =======================
    # CARGOS
    # =======================
    cargos = Cargosnodesados.objects.values(
        'id', 'id_cliente', 'valor', 'observacion',
        'fecha_ingreso', 'fecha_transaccion'
    )

    for c in cargos:
        cliente = Cliente.objects.filter(id=c["id_cliente"]).first()
        if not cliente:
            continue

        cid = cliente.id

        if cid not in clientes_data:
            clientes_data[cid] = {
                "cliente": cliente.nombre,
                "total": 0,
                "movimientos": [],
                "cotizador": []
            }

        movs = map_data([c], "Cargo no registrado", "Cargos no deseados")
        clientes_data[cid]["movimientos"] += movs
        clientes_data[cid]["total"] += safe_float(c["valor"])


    # =======================
    # ORDENAR MOVIMIENTOS
    # =======================
    for cid, info in clientes_data.items():
        info["movimientos"].sort(
            key=lambda x: parse_fecha(x.get("fecha")),
            reverse=True
        )

    return Response(list(clientes_data.values()), status=200)

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

[{'cliente':'el nombre', 'total':1234, 'datos':[{},{}]}]