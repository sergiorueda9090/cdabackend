from rest_framework.decorators  import api_view
from rest_framework.response    import Response
from rest_framework             import status
from recepcionPago.models       import RecepcionPago
from clientes.models            import Cliente
from .serializers               import RecepcionPagoSerializer
from registroTarjetas.models    import RegistroTarjetas


# 🔹 Listar todas las recepciones de pago
@api_view(['GET'])
def listar_recepciones_pago(request):
    recepciones = RecepcionPago.objects.all()
    serializer = RecepcionPagoSerializer(recepciones, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

# 🔹 Crear una nueva recepción de pago
@api_view(['POST'])
def crear_recepcion_pago(request):
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
        return Response({"error": "La tarjeta bancaria proporcionada no existe."}, status=status.HTTP_400_BAD_REQUEST)

    # Validar que la fecha de transacción no sea futura
    from datetime import date
    fecha_transaccion = request.data.get("fecha_transaccion")
    if date.fromisoformat(fecha_transaccion) > date.today():
        return Response({"error": "La fecha de transacción no puede ser en el futuro."}, status=status.HTTP_400_BAD_REQUEST)

    # Crear la recepción de pago
    recepcion = RecepcionPago.objects.create(
        cliente=cliente,
        id_tarjeta_bancaria=tarjeta,
        fecha_transaccion=request.data["fecha_transaccion"],
        valor=request.data["valor"],
        observacion=request.data.get("observacion", "")
    )

    serializer = RecepcionPagoSerializer(recepcion)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

# 🔹 Obtener una recepción de pago por ID
@api_view(['GET'])
def obtener_recepcion_pago(request, pk):
    try:
        recepcion = RecepcionPago.objects.get(pk=pk)
    except RecepcionPago.DoesNotExist:
        return Response({"error": "Recepción de pago no encontrada."}, status=status.HTTP_404_NOT_FOUND)

    serializer = RecepcionPagoSerializer(recepcion)
    return Response(serializer.data, status=status.HTTP_200_OK)

# 🔹 Actualizar una recepción de pago
@api_view(['PUT'])
def actualizar_recepcion_pago(request, pk):
    try:
        recepcion = RecepcionPago.objects.get(pk=pk)
    except RecepcionPago.DoesNotExist:
        return Response({"error": "Recepción de pago no encontrada."}, status=status.HTTP_404_NOT_FOUND)

    # Validar cliente si se envía en la solicitud
    cliente_id = request.data.get("cliente_id")
    if cliente_id:
        try:
            cliente = Cliente.objects.get(pk=cliente_id)
            recepcion.cliente = cliente
        except Cliente.DoesNotExist:
            return Response({"error": "El cliente proporcionado no existe."}, status=status.HTTP_400_BAD_REQUEST)

    # Validar tarjeta bancaria si se envía en la solicitud
    tarjeta_id = request.data.get("id_tarjeta_bancaria")
    if tarjeta_id:
        try:
            tarjeta = RegistroTarjetas.objects.get(pk=tarjeta_id)
            recepcion.id_tarjeta_bancaria = tarjeta
        except RegistroTarjetas.DoesNotExist:
            return Response({"error": "La tarjeta bancaria proporcionada no existe."}, status=status.HTTP_400_BAD_REQUEST)

    # Actualizar otros campos
    #recepcion.cuenta_bancaria_destino = request.data.get("cuenta_bancaria_destino", recepcion.cuenta_bancaria_destino)
    recepcion.fecha_transaccion = request.data.get("fecha_transaccion", recepcion.fecha_transaccion)
    recepcion.valor = request.data.get("valor", recepcion.valor)
    recepcion.observacion = request.data.get("observacion", recepcion.observacion)

    recepcion.save()

    serializer = RecepcionPagoSerializer(recepcion)
    return Response(serializer.data, status=status.HTTP_200_OK)

# 🔹 Eliminar una recepción de pago
@api_view(['DELETE'])
def eliminar_recepcion_pago(request, pk):
    try:
        recepcion = RecepcionPago.objects.get(pk=pk)
        recepcion.delete()
        return Response({"mensaje": "Recepción de pago eliminada correctamente."}, status=status.HTTP_204_NO_CONTENT)
    except RecepcionPago.DoesNotExist:
        return Response({"error": "Recepción de pago no encontrada."}, status=status.HTTP_404_NOT_FOUND)