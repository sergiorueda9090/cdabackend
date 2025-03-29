from django.shortcuts import get_object_or_404
from rest_framework.decorators  import api_view, permission_classes
from rest_framework.response    import Response
from rest_framework             import status
from ajustesaldos.models        import Ajustesaldo
from clientes.models            import Cliente

from rest_framework.permissions import IsAuthenticated

from .serializers               import AjustesaldoSerializer
from datetime import datetime
from django.db.models import Q

# 🔹 Listar todas las devoluciones
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_ajustessaldos(request):
    devolucionAll= Ajustesaldo.objects.all()
    devoluciones_pago_data = []

    for devolucion in devolucionAll:
        cliente = get_object_or_404(Cliente, id = devolucion.id_cliente_id)

        # Serializa cada recepción individualmente
        devolucion_serializer = AjustesaldoSerializer(devolucion)
        devolucion_data       = devolucion_serializer.data

        # Agregar datos personalizados
        devolucion_data['nombre_cliente'] = cliente.nombre
        devolucion_data['color_cliente']  = cliente.color
        devolucion_data['valor']          = abs(int(devolucion.valor))
        # Agregar la recepción modificada a la lista
        devoluciones_pago_data.append(devolucion_data)

    return Response(devoluciones_pago_data, status=status.HTTP_200_OK)

# 🔹 Crear una nueva devolución
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crear_ajustessaldo(request):
    required_fields = ["id_cliente", "fecha_transaccion", "valor"]

    # Validar que los campos requeridos estén en la petición
    for field in required_fields:
        if field not in request.data or not request.data[field]:
            return Response({"error": f"El campo '{field}' es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)

    # Validar que el cliente exista
    try:
        cliente = Cliente.objects.get(pk=request.data["id_cliente"])
    except Cliente.DoesNotExist:
        return Response({"error": "El cliente proporcionado no existe."}, status=status.HTTP_400_BAD_REQUEST)


    # Validar que la fecha de transacción no sea futura
    from datetime import date
    fecha_transaccion = request.data.get("fecha_transaccion")
    if date.fromisoformat(fecha_transaccion) > date.today():
        return Response({"error": "La fecha de transacción no puede ser en el futuro."}, status=status.HTTP_400_BAD_REQUEST)

    # Crear la devolución
    # Crear la devolución
    valor = request.data["valor"]
    valor = int(valor.replace(".", ""))
    valor = abs(valor)
    devolucionCreate = Ajustesaldo.objects.create(
        id_cliente          = cliente,
        fecha_transaccion   = fecha_transaccion,
        valor               = valor,
        observacion         = request.data.get("observacion", "")
    )

    serializer = AjustesaldoSerializer(devolucionCreate)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

# 🔹 Obtener una devolución por ID
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_ajustessaldo(request, pk):
    try:
        ajuesteSaldoGet = Ajustesaldo.objects.get(pk=pk)
    except Ajustesaldo.DoesNotExist:
        return Response({"error": "Ajuste de saldo no encontrada."}, status=status.HTTP_404_NOT_FOUND)
    
    ajuesteSaldoGet.valor = f"{abs(int(ajuesteSaldoGet.valor)):,}".replace(",", ".")
    serializer = AjustesaldoSerializer(ajuesteSaldoGet)
    return Response(serializer.data, status=status.HTTP_200_OK)

# 🔹 Actualizar una devolución
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def actualizar_ajustessaldo(request, pk):
    try:
        AjustesaldoGet = Ajustesaldo.objects.get(pk=pk)
    except Ajustesaldo.DoesNotExist:
        return Response({"error": "Ajuste de saldo no encontrada."}, status=status.HTTP_404_NOT_FOUND)

    cliente_id = request.data.get("cliente_id")
    if cliente_id:
        try:
            cliente = Cliente.objects.get(pk=cliente_id)
            AjustesaldoGet.cliente = cliente
        except Cliente.DoesNotExist:
            return Response({"error": "El cliente proporcionado no existe."}, status=status.HTTP_400_BAD_REQUEST)

    
    # Validar que la fecha de transacción no sea futura
    from datetime import date
    fecha_transaccion = request.data.get("fecha_transaccion")
    if date.fromisoformat(fecha_transaccion) > date.today():
        return Response({"error": "La fecha de transacción no puede ser en el futuro."}, status=status.HTTP_400_BAD_REQUEST)

    AjustesaldoGet.fecha_transaccion = request.data.get("fecha_transaccion", AjustesaldoGet.fecha_transaccion)
   

    valor = request.data.get("valor", AjustesaldoGet.valor)  # Obtener el valor del request o mantener el actual
    if isinstance(valor, str):                          # Si el valor es una cadena, limpiarlo
        valor = int(valor.replace(".", ""))             # Eliminar separadores de miles y convertir a número
    AjustesaldoGet.valor =  abs(valor)                      # Asegurar que siempre sea negativo

    AjustesaldoGet.observacion = request.data.get("observacion", AjustesaldoGet.observacion)

    AjustesaldoGet.save()

    serializer = AjustesaldoSerializer(AjustesaldoGet)
    return Response(serializer.data, status=status.HTTP_200_OK)

# 🔹 Eliminar una devolución
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def eliminar_ajustessaldo(request, pk):
    try:
        AjustesaldoDelete = Ajustesaldo.objects.get(pk=pk)
        AjustesaldoDelete.delete()
        return Response({"mensaje": "Ajuste de saldo eliminada correctamente."}, status=status.HTTP_204_NO_CONTENT)
    except Ajustesaldo.DoesNotExist:
        return Response({"error": "Ajuste de saldo no encontrada."}, status=status.HTTP_404_NOT_FOUND)

def parse_date_with_defaults(date_str, is_end=False):
    if not date_str:
        return None
    
    parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
    if is_end:
        parsed_date = parsed_date.replace(hour=23, minute=59, second=59)
    else:
        parsed_date = parsed_date.replace(hour=0, minute=0, second=0)
    return parsed_date


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_ajustessaldo_filtradas(request):
    fecha_inicio = parse_date_with_defaults(request.GET.get('fechaIncio'))
    fecha_fin    = parse_date_with_defaults(request.GET.get('fechaFin'), is_end=True)

    filtro_fecha = Q()
    if fecha_inicio and fecha_fin:
        filtro_fecha = Q(fecha_ingreso__range=(fecha_inicio, fecha_fin))
    elif fecha_inicio:
        filtro_fecha = Q(fecha_ingreso__gte=fecha_inicio)
    elif fecha_fin:
        filtro_fecha = Q(fecha_ingreso__lte=fecha_fin)

    devolucionAll= Ajustesaldo.objects.filter(filtro_fecha)
    devoluciones_pago_data = []

    for devolucion in devolucionAll:
        cliente = get_object_or_404(Cliente, id = devolucion.id_cliente_id)

        # Serializa cada recepción individualmente
        devolucion_serializer = AjustesaldoSerializer(devolucion)
        devolucion_data       = devolucion_serializer.data

        # Agregar datos personalizados
        devolucion_data['nombre_cliente'] = cliente.nombre
        devolucion_data['color_cliente']  = cliente.color

        # Agregar la recepción modificada a la lista
        devoluciones_pago_data.append(devolucion_data)

    return Response(devoluciones_pago_data, status=status.HTTP_200_OK)