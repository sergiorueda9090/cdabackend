from django.shortcuts           import get_object_or_404
from rest_framework.decorators  import api_view, permission_classes
from rest_framework.response    import Response
from rest_framework             import status

from utilidadocacional.models   import Utilidadocacional
from registroTarjetas.models    import RegistroTarjetas
from .serializers               import UtilidadocacionalSerializer

from rest_framework.permissions import IsAuthenticated

#Listar todas las recepciones de pago
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_utilidad_general(request):
    try:
        utilidades = Utilidadocacional.objects.all()
        total_utilidades_data = []

        for utilidad in utilidades:
            try:
                # Ensure we are getting the correct ID
                tarjeta_id = utilidad.id_tarjeta_bancaria.pk  # Get the numeric ID

                # Fetch related objects
                tarjeta = get_object_or_404(RegistroTarjetas, id=tarjeta_id)

                # Serialize gasto
                utilidad_serializer = UtilidadocacionalSerializer(utilidad)
                utilidad_data       = utilidad_serializer.data

                # Add extra data
                utilidad_data['nombre_tarjeta'] = tarjeta.nombre_cuenta

                # Append to result
                total_utilidades_data.append(utilidad_data)
            except Exception as e:
                return Response(
                    {"error": f"Error procesando recepción ID {tarjeta.id}: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(total_utilidades_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {"error": f"Error en la función total_utilidades_data: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Crear una nueva recepción de pago
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crear_utilidad_general(request):
    required_fields = ["id_tarjeta_bancaria", "fecha_transaccion", "valor"]

    # Validar que los campos requeridos estén en la petición
    for field in required_fields:
        if field not in request.data or not request.data[field]:
            return Response({"error": f"El campo '{field}' es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)

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
    recepcion_gasto_general = Utilidadocacional.objects.create(
        id_tarjeta_bancaria = tarjeta,
        fecha_transaccion   = request.data["fecha_transaccion"],
        valor               = request.data["valor"],
        observacion         = request.data.get("observacion", "")
    )

    serializer = UtilidadocacionalSerializer(recepcion_gasto_general)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

#Obtener una recepción de pago por ID
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_utilidad_general(request, pk):
    try:
        recepcion = Utilidadocacional.objects.get(pk=pk)
    except Utilidadocacional.DoesNotExist:
        return Response({"error": "Recepción de utilidad ocacional no encontrada."}, status=status.HTTP_404_NOT_FOUND)

    serializer = UtilidadocacionalSerializer(recepcion)
    return Response(serializer.data, status=status.HTTP_200_OK)

#Actualizar una recepción de pago
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def actualizar_utilidad_general(request, pk):
    try:
        recepcion = Utilidadocacional.objects.get(pk=pk)
    except Utilidadocacional.DoesNotExist:
        return Response({"error": "Recepción de utilidad ocacional no encontrada."}, status=status.HTTP_404_NOT_FOUND)

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
    recepcion.fecha_transaccion = request.data.get("fecha_transaccion"  , recepcion.fecha_transaccion)
    recepcion.valor             = request.data.get("valor"              , recepcion.valor)
    recepcion.observacion       = request.data.get("observacion"        , recepcion.observacion)

    recepcion.save()

    serializer = UtilidadocacionalSerializer(recepcion)
    return Response(serializer.data, status=status.HTTP_200_OK)

#Eliminar una recepción de pago
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def eliminar_utilidad_general(request, pk):
    try:
        recepcion = Utilidadocacional.objects.get(pk=pk)
        recepcion.delete()
        return Response({"mensaje": "Recepción de Utilidad ocacional eliminada correctamente."}, status=status.HTTP_204_NO_CONTENT)
    except Utilidadocacional.DoesNotExist:
        return Response({"error": "Recepción de Utilidad ocacional no encontrada."}, status=status.HTTP_404_NOT_FOUND)