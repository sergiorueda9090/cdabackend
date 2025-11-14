from django.shortcuts import get_object_or_404
from rest_framework.decorators  import api_view, permission_classes
from rest_framework.response    import Response
from rest_framework             import status

from gastosgenerales.models     import Gastogenerales
from gastos.models              import Gastos
from registroTarjetas.models    import RegistroTarjetas
from .serializers               import GastogeneralesSerializer

from rest_framework.permissions import IsAuthenticated

from datetime import datetime
from django.db.models   import Q
from users.decorators   import check_role
#Listar todas las recepciones de pago
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1,2)
def listar_gastos_generales(request):
    try:
        gastos = Gastogenerales.objects.all().order_by('-fecha_ingreso')
        total_gastos_data = []

        for gasto in gastos:
            try:
                # Ensure we are getting the correct ID
                tarjeta_id = gasto.id_tarjeta_bancaria.pk  # Get the numeric ID
                gasto_id   = gasto.id_tipo_gasto.pk
                
                gasto.valor = abs(int(gasto.valor))
                # Fetch related objects
                tarjeta     = get_object_or_404(RegistroTarjetas, id=tarjeta_id)
                gasto_model = get_object_or_404(Gastos, id=gasto_id)

                # Serialize gasto
                gastos_serializer = GastogeneralesSerializer(gasto)
                gastos_data = gastos_serializer.data
                
                # Add extra data
                gastos_data['nombre_tarjeta'] = tarjeta.nombre_cuenta
                gastos_data['nombre_gasto'] = gasto_model.name

                # Append to result
                total_gastos_data.append(gastos_data)
                print("total_gastos_data ",total_gastos_data)
            except Exception as e:
                print(f"Error procesando recepción ID {gasto.id}: {e}")
                return Response(
                    {"error": f"Error procesando recepción ID {gasto.id}: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(total_gastos_data, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"Error en la función listar_gastos_generales: {e}")
        return Response(
            {"error": f"Error en la función listar_gastos_generales: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Crear una nueva recepción de pago
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@check_role(1,2)
def crear_gasto_generale(request):
    required_fields = ["id_tipo_gasto", "id_tarjeta_bancaria", "fecha_transaccion", "valor"]

    # Validar que los campos requeridos estén en la petición
    for field in required_fields:
        if field not in request.data or not request.data[field]:
            return Response({"error": f"El campo '{field}' es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)

    # Validar que el cliente exista
    try:
        gasto = Gastos.objects.get(pk=request.data["id_tipo_gasto"])
    except Gastos.DoesNotExist:
        return Response({"error": "El Gasto proporcionado no existe."}, status=status.HTTP_400_BAD_REQUEST)

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
    valor = request.data["valor"]
    valor = int(valor.replace(".", ""))
    valor = -abs(valor)

    if tarjeta.is_daviplata:
        cuatro_por_mil = 0
    else:
        cuatro_por_mil = int(abs(valor) * 0.004)
    
    recepcion_gasto_general = Gastogenerales.objects.create(
        id_tipo_gasto       = gasto,
        id_tarjeta_bancaria = tarjeta,
        fecha_transaccion   = request.data["fecha_transaccion"],
        valor               = valor,
        cuatro_por_mil      = cuatro_por_mil,
        observacion         = request.data.get("observacion", "")
    )

    serializer = GastogeneralesSerializer(recepcion_gasto_general)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

#Obtener una recepción de pago por ID
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1,2)
def obtener_gasto_generale(request, pk):
    try:
        recepcion = Gastogenerales.objects.get(pk=pk)
    except Gastogenerales.DoesNotExist:
        return Response({"error": "Recepción de gastos generales no encontrada."}, status=status.HTTP_404_NOT_FOUND)
    recepcion.valor = f"{abs(int(recepcion.valor)):,}".replace(",", ".")
    serializer = GastogeneralesSerializer(recepcion)
    return Response(serializer.data, status=status.HTTP_200_OK)

#Actualizar una recepción de pago
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@check_role(1,2)
def actualizar_gasto_generale(request, pk):
    try:
        recepcion = Gastogenerales.objects.get(pk=pk)
    except Gastogenerales.DoesNotExist:
        return Response({"error": "Recepción de gastos generales no encontrada."}, status=status.HTTP_404_NOT_FOUND)

    # Validar cliente si se envía en la solicitud
    id_tipo_gasto = request.data.get("id_tipo_gasto")
    if id_tipo_gasto:
        try:
            gasto = Gastos.objects.get(pk=id_tipo_gasto)
            recepcion.id_tipo_gasto = gasto
        except Gastos.DoesNotExist:
            return Response({"error": "El gasto proporcionado no existe."}, status=status.HTTP_400_BAD_REQUEST)

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
    if isinstance(valor, str):  # Si el valor es una cadena, limpiarlo
        valor = int(valor.replace(".", ""))  # Eliminar separadores de miles y convertir a número
    
    recepcion.valor         =  -abs(valor)  # Asegurar que siempre sea negativo
    recepcion.observacion   = request.data.get("observacion", recepcion.observacion)

    if tarjeta.is_daviplata:
        recepcion.cuatro_por_mil = 0
    else:
        recepcion.cuatro_por_mil = int(abs(valor) * 0.004)

    recepcion.save()

    serializer = GastogeneralesSerializer(recepcion)
    return Response(serializer.data, status=status.HTTP_200_OK)

#Eliminar una recepción de pago
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@check_role(1,2)
def eliminar_gasto_generale(request, pk):
    try:
        recepcion = Gastogenerales.objects.get(pk=pk)
        recepcion.delete()
        return Response({"mensaje": "Recepción de Gasto generale eliminada correctamente."}, status=status.HTTP_204_NO_CONTENT)
    except Gastogenerales.DoesNotExist:
        return Response({"error": "Recepción de Gasto generale no encontrada."}, status=status.HTTP_404_NOT_FOUND)
    

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
@check_role(1,2)
def listar_gastos_generales_filtradas(request):
    fecha_inicio = parse_date_with_defaults(request.GET.get('fechaInicio'))
    fecha_fin    = parse_date_with_defaults(request.GET.get('fechaFin'), is_end=True)

    filtro_fecha = Q()
    if fecha_inicio and fecha_fin:
        filtro_fecha = Q(fecha_ingreso__range=(fecha_inicio, fecha_fin))
    elif fecha_inicio:
        filtro_fecha = Q(fecha_ingreso__gte=fecha_inicio)
    elif fecha_fin:
        filtro_fecha = Q(fecha_ingreso__lte=fecha_fin)

    try:
        gastos = Gastogenerales.objects.filter(filtro_fecha)
        total_gastos_data = []

        for gasto in gastos:
            try:
                # Ensure we are getting the correct ID
                tarjeta_id = gasto.id_tarjeta_bancaria.pk  # Get the numeric ID
                gasto_id   = gasto.id_tipo_gasto.pk

                # Fetch related objects
                tarjeta     = get_object_or_404(RegistroTarjetas, id=tarjeta_id)
                gasto_model = get_object_or_404(Gastos, id=gasto_id)

                # Serialize gasto
                gastos_serializer = GastogeneralesSerializer(gasto)
                gastos_data = gastos_serializer.data

                # Add extra data
                gastos_data['nombre_tarjeta'] = tarjeta.nombre_cuenta
                gastos_data['nombre_gasto'] = gasto_model.name

                # Append to result
                total_gastos_data.append(gastos_data)
                print("total_gastos_data ",total_gastos_data)
            except Exception as e:
                print(f"Error procesando recepción ID {gasto.id}: {e}")
                return Response(
                    {"error": f"Error procesando recepción ID {gasto.id}: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(total_gastos_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {"error": f"Error en la función total_utilidades_data: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )