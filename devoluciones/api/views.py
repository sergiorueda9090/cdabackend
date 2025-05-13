from django.utils.dateparse import parse_date
from django.shortcuts import get_object_or_404
from rest_framework.decorators  import api_view
from rest_framework.response    import Response
from rest_framework             import status
from devoluciones.models        import Devoluciones

from clientes.models            import Cliente
from registroTarjetas.models    import RegistroTarjetas

from .serializers               import DevolucionesSerializer
from users.decorators           import check_role

# 🔹 Listar todas las devoluciones
@api_view(['GET'])
@check_role(1)
def listar_devoluciones(request):
    devolucionAll= Devoluciones.objects.all()
    devoluciones_pago_data = []

    for devolucion in devolucionAll:
        tarjeta = get_object_or_404(RegistroTarjetas,    id = devolucion.id_tarjeta_bancaria_id)
        cliente = get_object_or_404(Cliente,             id = devolucion.id_cliente_id)

        # Serializa cada recepción individualmente
        devolucion_serializer = DevolucionesSerializer(devolucion)
        devolucion_data       = devolucion_serializer.data

        # Agregar datos personalizados
        devolucion_data['nombre_tarjeta'] = tarjeta.nombre_cuenta
        devolucion_data['nombre_cliente'] = cliente.nombre
        devolucion_data['color_cliente']  = cliente.color
        devolucion_data['valor']          = abs(int(devolucion.valor))

        cuatro_por_mil = devolucion.cuatro_por_mil
        if not cuatro_por_mil:
            cuatro_por_mil = 0

        devolucion_data['total'] = abs(int(devolucion.valor)) - abs(int(cuatro_por_mil))
        # Agregar la recepción modificada a la lista
        devoluciones_pago_data.append(devolucion_data)

    return Response(devoluciones_pago_data, status=status.HTTP_200_OK)

# 🔹 Crear una nueva devolución
@api_view(['POST'])
@check_role(1)
def crear_devolucion(request):
    required_fields = ["id_cliente", "id_tarjeta_bancaria", "fecha_transaccion", "valor"]

    # Validar que los campos requeridos estén en la petición
    for field in required_fields:
        if field not in request.data or not request.data[field]:
            return Response({"error": f"El campo '{field}' es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)

    # Validar que el cliente exista
    try:
        cliente = Cliente.objects.get(pk=request.data["id_cliente"])
    except Cliente.DoesNotExist:
        return Response({"error": "El cliente proporcionado no existe."}, status=status.HTTP_400_BAD_REQUEST)

    # Validar que la tarjeta bancaria exista
    try:
        tarjeta = RegistroTarjetas.objects.get(pk=request.data["id_tarjeta_bancaria"])
    except RegistroTarjetas.DoesNotExist:
        return Response({"error": "La cuenta bancaria proporcionada no existe."}, status=status.HTTP_400_BAD_REQUEST)

    # Validar que la fecha de transacción no sea futura
    from datetime import date
    fecha_transaccion = request.data.get("fecha_transaccion")
    if date.fromisoformat(fecha_transaccion) > date.today():
        return Response({"error": "La fecha de transacción no puede ser en el futuro."}, status=status.HTTP_400_BAD_REQUEST)

    # Crear la devolución
    valor = request.data["valor"]
    valor = int(valor.replace(".", ""))
    valor = -abs(valor)

    if tarjeta.is_daviplata:
        cuatro_por_mil = 0
    else:
        cuatro_por_mil = int(abs(valor) * 0.004)

    devolucionCreate = Devoluciones.objects.create(
        id_cliente          = cliente,
        id_tarjeta_bancaria = tarjeta,
        fecha_transaccion   = fecha_transaccion,
        valor               = valor,
        cuatro_por_mil      = cuatro_por_mil,
        observacion         = request.data.get("observacion", "")
    )

    serializer = DevolucionesSerializer(devolucionCreate)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

# 🔹 Obtener una devolución por ID
@api_view(['GET'])
@check_role(1)
def obtener_devolucion(request, pk):
    try:
        devolucionGet = Devoluciones.objects.get(pk=pk)
    except Devoluciones.DoesNotExist:
        return Response({"error": "Devolución no encontrada."}, status=status.HTTP_404_NOT_FOUND)
    
    devolucionGet.valor = f"{abs(int(devolucionGet.valor)):,}".replace(",", ".")
    serializer = DevolucionesSerializer(devolucionGet)
    return Response(serializer.data, status=status.HTTP_200_OK)

# 🔹 Actualizar una devolución
@api_view(['PUT'])
@check_role(1)
def actualizar_devolucion(request, pk):
    try:
        devolucionGet = Devoluciones.objects.get(pk=pk)
    except Devoluciones.DoesNotExist:
        return Response({"error": "Devolución no encontrada."}, status=status.HTTP_404_NOT_FOUND)

    cliente_id = request.data.get("cliente_id")
    if cliente_id:
        try:
            cliente = Cliente.objects.get(pk=cliente_id)
            devolucionGet.cliente = cliente
        except Cliente.DoesNotExist:
            return Response({"error": "El cliente proporcionado no existe."}, status=status.HTTP_400_BAD_REQUEST)

    tarjeta_id = request.data.get("id_tarjeta_bancaria")
    if tarjeta_id:
        try:
            tarjeta = RegistroTarjetas.objects.get(pk=tarjeta_id)
            devolucionGet.id_tarjeta_bancaria = tarjeta
        except RegistroTarjetas.DoesNotExist:
            return Response({"error": "La cuenta bancaria proporcionada no existe."}, status=status.HTTP_400_BAD_REQUEST)
    
    # Validar que la fecha de transacción no sea futura
    from datetime import date
    fecha_transaccion = request.data.get("fecha_transaccion")
    if date.fromisoformat(fecha_transaccion) > date.today():
        return Response({"error": "La fecha de transacción no puede ser en el futuro."}, status=status.HTTP_400_BAD_REQUEST)

    devolucionGet.fecha_transaccion = request.data.get("fecha_transaccion", devolucionGet.fecha_transaccion)
 
    
    valor = request.data.get("valor", devolucionGet.valor)  # Obtener el valor del request o mantener el actual
    if isinstance(valor, str):  # Si el valor es una cadena, limpiarlo
        valor = int(valor.replace(".", ""))  # Eliminar separadores de miles y convertir a número
    devolucionGet.valor =  -abs(valor)  # Asegurar que siempre sea negativo
    
    devolucionGet.observacion = request.data.get("observacion", devolucionGet.observacion)

    if tarjeta.is_daviplata:
        devolucionGet.cuatro_por_mil = 0
    else:
        devolucionGet.cuatro_por_mil = int(abs(valor) * 0.004)
                                       
    devolucionGet.save()

    serializer = DevolucionesSerializer(devolucionGet)
    return Response(serializer.data, status=status.HTTP_200_OK)

# 🔹 Eliminar una devolución
@api_view(['DELETE'])
@check_role(1)
def eliminar_devolucion(request, pk):
    try:
        devolucionDelete = Devoluciones.objects.get(pk=pk)
        devolucionDelete.delete()
        return Response({"mensaje": "Devolución eliminada correctamente."}, status=status.HTTP_204_NO_CONTENT)
    except Devoluciones.DoesNotExist:
        return Response({"error": "Devolución no encontrada."}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@check_role(1)
def listar_devoluciones_filtro(request):
    from datetime import datetime, time
    fecha_inicio_str = request.GET.get('fechaInicio')
    fecha_fin_str    = request.GET.get('fechaFin')

    if not fecha_inicio_str or not fecha_fin_str:
        return Response({'error': 'Debe proporcionar fechaInicio y fechaFin como parámetros.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        fecha_inicio_date = parse_date(fecha_inicio_str)
        fecha_fin_date = parse_date(fecha_fin_str)

        # Convertir a datetime con horas ajustadas
        fecha_inicio = datetime.combine(fecha_inicio_date, time.min)  # 00:00:00
        fecha_fin = datetime.combine(fecha_fin_date, time.max)        # 23:59:59.999999

    except (ValueError, TypeError):
        return Response({'error': 'Formato de fecha inválido. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

    devolucionAll = Devoluciones.objects.filter(fecha_transaccion__range=[fecha_inicio, fecha_fin])
    devoluciones_pago_data = []

    for devolucion in devolucionAll:
        tarjeta = get_object_or_404(RegistroTarjetas, id=devolucion.id_tarjeta_bancaria_id)
        cliente = get_object_or_404(Cliente, id=devolucion.id_cliente_id)

        devolucion_serializer = DevolucionesSerializer(devolucion)
        devolucion_data = devolucion_serializer.data

        devolucion_data['nombre_tarjeta'] = tarjeta.nombre_cuenta
        devolucion_data['nombre_cliente'] = cliente.nombre
        devolucion_data['color_cliente'] = cliente.color
        devolucion_data['valor'] = abs(int(devolucion.valor))

        cuatro_por_mil = devolucion.cuatro_por_mil
        if not cuatro_por_mil:
            cuatro_por_mil = 0

        devolucion_data['total'] = devolucion_data['valor'] - abs(int(cuatro_por_mil))

        devoluciones_pago_data.append(devolucion_data)

    return Response(devoluciones_pago_data, status=status.HTTP_200_OK)