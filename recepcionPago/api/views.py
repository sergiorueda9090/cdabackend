from django.shortcuts import get_object_or_404
from rest_framework.decorators  import api_view, permission_classes
from rest_framework.response    import Response
from rest_framework             import status
from recepcionPago.models       import RecepcionPago
from clientes.models            import Cliente
from registroTarjetas.models    import RegistroTarjetas
from .serializers               import RecepcionPagoSerializer

from rest_framework.permissions import IsAuthenticated


from django.db.models   import Q
from datetime import date, datetime

#Listar todas las recepciones de pago
@api_view(['GET'])
def listar_recepciones_pago(request):
    try:
        recepciones = RecepcionPago.objects.all()
        total_recepciones = recepciones.count()
        print(f"Total recepciones: {total_recepciones}")


        recepciones_pago_data = []

        for recepcion in recepciones:
            try:
                print(f"Procesando recepción ID: {recepcion.id}")

                # Intentamos obtener la tarjeta y el cliente
                tarjeta = get_object_or_404(RegistroTarjetas, id=recepcion.id_tarjeta_bancaria_id)
                cliente = get_object_or_404(Cliente, id=recepcion.cliente_id)


                # Serializa la recepción
                recepcion_serializer = RecepcionPagoSerializer(recepcion)
                recepcion_data = recepcion_serializer.data

                # Agregar datos adicionales
                recepcion_data['nombre_tarjeta']    = tarjeta.nombre_cuenta
                recepcion_data['nombre_cliente']    = cliente.nombre
                recepcion_data['color_cliente']     = cliente.color
                recepcion_data['valor']             = abs(int(recepcion.valor))
                # Agregar al listado
                recepciones_pago_data.append(recepcion_data)

            except Exception as e:
                print(f"Error procesando recepción ID {recepcion.id}: {e}")
                return Response(
                    {"error": f"Error procesando recepción ID {recepcion.id}: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(recepciones_pago_data, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"Error en la función listar_recepciones_pago: {e}")
        return Response(
            {"error": f"Error en la función listar_recepciones_pago: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Crear una nueva recepción de pago
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crear_recepcion_pago(request):
    required_fields = ["cliente_id", "id_tarjeta_bancaria", "fecha_transaccion", "valor"]

    for field in required_fields:
        if field not in request.data or not request.data[field]:
            return Response({"error": f"El campo '{field}' es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        cliente = Cliente.objects.get(pk=request.data["cliente_id"])
    except Cliente.DoesNotExist:
        return Response({"error": "El cliente proporcionado no existe."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        tarjeta = RegistroTarjetas.objects.get(pk=request.data["id_tarjeta_bancaria"])
    except RegistroTarjetas.DoesNotExist:
        return Response({"error": "La tarjeta bancaria proporcionada no existe."}, status=status.HTTP_400_BAD_REQUEST)

    fecha_transaccion_str = request.data.get("fecha_transaccion")
    print(fecha_transaccion_str)
    try:
        # Espera un string como: "2025-04-07 19:31:17.730203"
        fecha_transaccion = datetime.strptime(fecha_transaccion_str, "%Y-%m-%d %H:%M:%S.%f")
    except (ValueError, TypeError):
        return Response({"error": "La fecha de transacción no es válida."}, status=status.HTTP_400_BAD_REQUEST)

    #if fecha_transaccion > date.today():
    #    return Response({"error": "La fecha de transacción no puede ser en el futuro."}, status=status.HTTP_400_BAD_REQUEST)

    # Convertir el valor a entero
    valor = request.data["valor"]
    valor = int(valor.replace(".", ""))
    valor = abs(valor)

    # Validación de duplicado
    confirmar = request.data.get("confirmar", "false").lower() == "true"

    if not confirmar:
        pago_duplicado = RecepcionPago.objects.filter(
            cliente=cliente,
            valor=valor,
            fecha_transaccion=fecha_transaccion
        ).exists()

        if pago_duplicado:
            return Response({
                "advertencia": "¿Estás seguro que deseas ingresar este pago? Ya existe un pago para este cliente por el mismo valor el día de hoy.",
                "requiere_confirmacion": True
            }, status=status.HTTP_200_OK)

    # Crear la recepción de pago
    recepcion = RecepcionPago.objects.create(
        cliente=cliente,
        id_tarjeta_bancaria=tarjeta,
        fecha_transaccion=fecha_transaccion,
        valor=valor,
        observacion=request.data.get("observacion", "")
    )

    serializer = RecepcionPagoSerializer(recepcion)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

#Obtener una recepción de pago por ID
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_recepcion_pago(request, pk):
    try:
        recepcion = RecepcionPago.objects.get(pk=pk)
    except RecepcionPago.DoesNotExist:
        return Response({"error": "Recepción de pago no encontrada."}, status=status.HTTP_404_NOT_FOUND)
    
    recepcion.valor = f"{abs(int(recepcion.valor)):,}".replace(",", ".")
    serializer = RecepcionPagoSerializer(recepcion)
    return Response(serializer.data, status=status.HTTP_200_OK)

#Actualizar una recepción de pago
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
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
   
    valor = request.data.get("valor", recepcion.valor)  # Obtener el valor del request o mantener el actual
    if isinstance(valor, str):                          # Si el valor es una cadena, limpiarlo
        valor = int(valor.replace(".", ""))             # Eliminar separadores de miles y convertir a número
    recepcion.valor =  abs(valor)                      # Asegurar que siempre sea negativo
   
    recepcion.observacion = request.data.get("observacion", recepcion.observacion)

    recepcion.save()

    serializer = RecepcionPagoSerializer(recepcion)
    return Response(serializer.data, status=status.HTTP_200_OK)

#Eliminar una recepción de pago
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def eliminar_recepcion_pago(request, pk):
    try:
        recepcion = RecepcionPago.objects.get(pk=pk)
        recepcion.delete()
        return Response({"mensaje": "Recepción de pago eliminada correctamente."}, status=status.HTTP_204_NO_CONTENT)
    except RecepcionPago.DoesNotExist:
        return Response({"error": "Recepción de pago no encontrada."}, status=status.HTTP_404_NOT_FOUND)
    

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
def listar_recepciones_pago_filtradas(request):
    fecha_inicio = parse_date_with_defaults(request.GET.get('fechaIncio'))
    fecha_fin    = parse_date_with_defaults(request.GET.get('fechaFin'), is_end=True)

    filtro_fecha = Q()
    if fecha_inicio and fecha_fin:
        filtro_fecha = Q(fecha_ingreso__range=(fecha_inicio, fecha_fin))
    elif fecha_inicio:
        filtro_fecha = Q(fecha_ingreso__gte=fecha_inicio)
    elif fecha_fin:
        filtro_fecha = Q(fecha_ingreso__lte=fecha_fin)

    try:
        recepciones = RecepcionPago.objects.filter(filtro_fecha)
        total_recepciones = recepciones.count()

        recepciones_pago_data = []

        for recepcion in recepciones:
            try:
                # Intentamos obtener la tarjeta y el cliente
                tarjeta = get_object_or_404(RegistroTarjetas, id=recepcion.id_tarjeta_bancaria_id)
                cliente = get_object_or_404(Cliente, id=recepcion.cliente_id)
                # Serializa la recepción
                recepcion_serializer = RecepcionPagoSerializer(recepcion)
                recepcion_data = recepcion_serializer.data

                # Agregar datos adicionales
                recepcion_data['nombre_tarjeta'] = tarjeta.nombre_cuenta
                recepcion_data['nombre_cliente'] = cliente.nombre
                recepcion_data['color_cliente'] = cliente.color

                # Agregar al listado
                recepciones_pago_data.append(recepcion_data)

            except Exception as e:
                print(f"Error procesando recepción ID {recepcion.id}: {e}")
                return Response(
                    {"error": f"Error procesando recepción ID {recepcion.id}: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(recepciones_pago_data, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"Error en la función listar_recepciones_pago: {e}")
        return Response(
            {"error": f"Error en la función listar_recepciones_pago: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )