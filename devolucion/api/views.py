from rest_framework.decorators  import api_view
from rest_framework.response    import Response
from rest_framework             import status
from devolucion.models          import Devolucion
from .serializers               import DevolucionSerializer
from clientes.models            import Cliente
from registroTarjetas.models    import RegistroTarjetas

# 🔹 Listar todas las devoluciones
@api_view(['GET'])
def listar_devoluciones(request):
    devoluciones = Devolucion.objects.all()
    serializer   = DevolucionSerializer(devoluciones, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

# 🔹 Crear una nueva devolución
@api_view(['POST'])
def crear_devolucion(request):
    required_fields = ["cliente_id", "id_tarjeta_bancaria", "fecha_transaccion", "valor"]

    # Validar que los campos requeridos estén en la petición
    for field in required_fields:
        if field not in request.data or not request.data[field]:
            return Response({"error": f"El campo '{field}' es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)

    # Validar que el cliente exista
    try:
        cliente = Cliente.objects.get(pk=request.data["cliente_id"])
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
    devolucion = Devolucion.objects.create(
        cliente             = cliente,
        id_tarjeta_bancaria = tarjeta,
        fecha_transaccion   = fecha_transaccion,
        valor               = request.data["valor"],
        observacion         = request.data.get("observacion", "")
    )

    serializer = DevolucionSerializer(devolucion)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

# 🔹 Obtener una devolución por ID
@api_view(['GET'])
def obtener_devolucion(request, pk):
    try:
        devolucion = Devolucion.objects.get(pk=pk)
    except Devolucion.DoesNotExist:
        return Response({"error": "Devolución no encontrada."}, status=status.HTTP_404_NOT_FOUND)

    serializer = DevolucionSerializer(devolucion)
    return Response(serializer.data, status=status.HTTP_200_OK)

# 🔹 Actualizar una devolución
@api_view(['PUT'])
def actualizar_devolucion(request, pk):
    try:
        devolucion = Devolucion.objects.get(pk=pk)
    except Devolucion.DoesNotExist:
        return Response({"error": "Devolución no encontrada."}, status=status.HTTP_404_NOT_FOUND)

    cliente_id = request.data.get("cliente_id")
    if cliente_id:
        try:
            cliente = Cliente.objects.get(pk=cliente_id)
            devolucion.cliente = cliente
        except Cliente.DoesNotExist:
            return Response({"error": "El cliente proporcionado no existe."}, status=status.HTTP_400_BAD_REQUEST)

    tarjeta_id = request.data.get("id_tarjeta_bancaria")
    if tarjeta_id:
        try:
            tarjeta = RegistroTarjetas.objects.get(pk=tarjeta_id)
            devolucion.id_tarjeta_bancaria = tarjeta
        except RegistroTarjetas.DoesNotExist:
            return Response({"error": "La cuenta bancaria proporcionada no existe."}, status=status.HTTP_400_BAD_REQUEST)
    
    # Validar que la fecha de transacción no sea futura
    from datetime import date
    fecha_transaccion = request.data.get("fecha_transaccion")
    if date.fromisoformat(fecha_transaccion) > date.today():
        return Response({"error": "La fecha de transacción no puede ser en el futuro."}, status=status.HTTP_400_BAD_REQUEST)

    devolucion.fecha_transaccion = request.data.get("fecha_transaccion", recepcion.fecha_transaccion)
    devolucion.valor = request.data.get("valor", devolucion.valor)
    devolucion.observacion = request.data.get("observacion", devolucion.observacion)

    devolucion.save()

    serializer = DevolucionSerializer(devolucion)
    return Response(serializer.data, status=status.HTTP_200_OK)

# 🔹 Eliminar una devolución
@api_view(['DELETE'])
def eliminar_devolucion(request, pk):
    try:
        devolucion = Devolucion.objects.get(pk=pk)
        devolucion.delete()
        return Response({"mensaje": "Devolución eliminada correctamente."}, status=status.HTTP_204_NO_CONTENT)
    except Devolucion.DoesNotExist:
        return Response({"error": "Devolución no encontrada."}, status=status.HTTP_404_NOT_FOUND)
