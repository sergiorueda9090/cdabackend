from django.shortcuts import get_object_or_404
from rest_framework.decorators  import api_view
from rest_framework.response    import Response
from rest_framework             import status
from ajustesaldos.models        import Ajustesaldo
from clientes.models            import Cliente

from .serializers               import AjustesaldoSerializer

# 🔹 Listar todas las devoluciones
@api_view(['GET'])
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

        # Agregar la recepción modificada a la lista
        devoluciones_pago_data.append(devolucion_data)

    return Response(devoluciones_pago_data, status=status.HTTP_200_OK)

# 🔹 Crear una nueva devolución
@api_view(['POST'])
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
    devolucionCreate = Ajustesaldo.objects.create(
        id_cliente          = cliente,
        fecha_transaccion   = fecha_transaccion,
        valor               = request.data["valor"],
        observacion         = request.data.get("observacion", "")
    )

    serializer = AjustesaldoSerializer(devolucionCreate)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

# 🔹 Obtener una devolución por ID
@api_view(['GET'])
def obtener_ajustessaldo(request, pk):
    try:
        ajuesteSaldoGet = Ajustesaldo.objects.get(pk=pk)
    except Ajustesaldo.DoesNotExist:
        return Response({"error": "Ajuste de saldo no encontrada."}, status=status.HTTP_404_NOT_FOUND)

    serializer = AjustesaldoSerializer(ajuesteSaldoGet)
    return Response(serializer.data, status=status.HTTP_200_OK)

# 🔹 Actualizar una devolución
@api_view(['PUT'])
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
    AjustesaldoGet.valor = request.data.get("valor", AjustesaldoGet.valor)
    AjustesaldoGet.observacion = request.data.get("observacion", AjustesaldoGet.observacion)

    AjustesaldoGet.save()

    serializer = AjustesaldoSerializer(AjustesaldoGet)
    return Response(serializer.data, status=status.HTTP_200_OK)

# 🔹 Eliminar una devolución
@api_view(['DELETE'])
def eliminar_ajustessaldo(request, pk):
    try:
        AjustesaldoDelete = Ajustesaldo.objects.get(pk=pk)
        AjustesaldoDelete.delete()
        return Response({"mensaje": "Ajuste de saldo eliminada correctamente."}, status=status.HTTP_204_NO_CONTENT)
    except Ajustesaldo.DoesNotExist:
        return Response({"error": "Ajuste de saldo no encontrada."}, status=status.HTTP_404_NOT_FOUND)
