from django.shortcuts           import get_object_or_404
from rest_framework.decorators  import api_view, permission_classes
from rest_framework.response    import Response
from rest_framework             import status

from utilidadocacional.models   import Utilidadocacional
from registroTarjetas.models    import RegistroTarjetas
from .serializers               import UtilidadocacionalSerializer

from rest_framework.permissions import IsAuthenticated

from datetime           import datetime
from django.db.models   import Q
from users.decorators   import check_role
#Listar todas las recepciones de pago
# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# @check_role(1)
# def listar_utilidad_general(request):
#     try:
#         utilidades = Utilidadocacional.objects.all()
#         total_utilidades_data = []

#         for utilidad in utilidades:
#             try:
#                 # Ensure we are getting the correct ID
#                 tarjeta_id = utilidad.id_tarjeta_bancaria.pk  # Get the numeric ID

#                 # Fetch related objects
#                 tarjeta = get_object_or_404(RegistroTarjetas, id=tarjeta_id)

#                 # Serialize gasto
#                 utilidad_serializer = UtilidadocacionalSerializer(utilidad)
#                 utilidad_data       = utilidad_serializer.data

#                 # Add extra data
#                 utilidad_data['nombre_tarjeta'] = tarjeta.nombre_cuenta
#                 utilidad_data['valor']          = abs(int(utilidad.valor))

#                 cuatro_por_mil = utilidad.cuatro_por_mil
#                 if not cuatro_por_mil:
#                     cuatro_por_mil = 0

#                 utilidad_data['total'] = utilidad_data['valor'] - abs(int(cuatro_por_mil))

#                 # Append to result
#                 total_utilidades_data.append(utilidad_data)
#             except Exception as e:
#                 return Response(
#                     {"error": f"Error procesando recepción ID {tarjeta.id}: {str(e)}"},
#                     status=status.HTTP_500_INTERNAL_SERVER_ERROR
#                 )

#         return Response(total_utilidades_data, status=status.HTTP_200_OK)

#     except Exception as e:
#         return Response(
#             {"error": f"Error en la función total_utilidades_data: {str(e)}"},
#             status=status.HTTP_500_INTERNAL_SERVER_ERROR
#         )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1,2)
def listar_utilidad_general(request):
    try:
        utilidades = Utilidadocacional.objects.all().order_by('-fecha_ingreso')
        total_utilidades_data = []

        for utilidad in utilidades:
            try:
                # Obtener la tarjeta asociada
                tarjeta = get_object_or_404(RegistroTarjetas, id=utilidad.id_tarjeta_bancaria.pk)

                # Serializar utilidad
                utilidad_serializer = UtilidadocacionalSerializer(utilidad)
                utilidad_data = utilidad_serializer.data

                # Agregar datos adicionales
                utilidad_data['nombre_tarjeta'] = tarjeta.nombre_cuenta

                # Convertir valor y cuatro_por_mil a enteros
                valor = int(utilidad.valor)
                cuatro_por_mil = int(utilidad.cuatro_por_mil or 0)

                # Calcular total manteniendo el signo correcto
                if valor >= 0:
                    total = valor - cuatro_por_mil
                else:
                    total = valor + cuatro_por_mil

                utilidad_data['valor'] = valor
                utilidad_data['cuatro_por_mil'] = cuatro_por_mil
                utilidad_data['total'] = total

                total_utilidades_data.append(utilidad_data)

            except Exception as e:
                return Response(
                    {"error": f"Error procesando utilidad ID {utilidad.id}: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(total_utilidades_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {"error": f"Error al listar utilidades: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Crear una nueva recepción de pago
# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# @check_role(1)
# def crear_utilidad_general(request):
#     required_fields = ["id_tarjeta_bancaria", "fecha_transaccion", "valor"]

#     # Validar que los campos requeridos estén en la petición
#     for field in required_fields:
#         if field not in request.data or not request.data[field]:
#             return Response({"error": f"El campo '{field}' es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)

#     # Validar que la tarjeta bancaria exista
#     try:
#         tarjeta = RegistroTarjetas.objects.get(pk=request.data["id_tarjeta_bancaria"])
#     except RegistroTarjetas.DoesNotExist:
#         return Response({"error": "La tarjeta bancaria proporcionada no existe."}, status=status.HTTP_400_BAD_REQUEST)

#     # Validar que la fecha de transacción no sea futura
#     from datetime import date
#     fecha_transaccion = request.data.get("fecha_transaccion")
#     if date.fromisoformat(fecha_transaccion) > date.today():
#         return Response({"error": "La fecha de transacción no puede ser en el futuro."}, status=status.HTTP_400_BAD_REQUEST)

#     # Crear la recepción de pago
#     # Crear la devolución
#     valor = request.data["valor"]
#     valor = int(valor.replace(".", ""))
#     valor = abs(valor)

#     if tarjeta.is_daviplata:
#         cuatro_por_mil = 0
#     else:
#         cuatro_por_mil = int(abs(valor) * 0.004)
    
#     recepcion_gasto_general = Utilidadocacional.objects.create(
#         id_tarjeta_bancaria = tarjeta,
#         fecha_transaccion   = request.data["fecha_transaccion"],
#         valor               = valor,
#         cuatro_por_mil      = cuatro_por_mil,
#         observacion         = request.data.get("observacion", "")
#     )

#     serializer = UtilidadocacionalSerializer(recepcion_gasto_general)
#     return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@check_role(1,2)
def crear_utilidad_general(request):
    required_fields = ["id_tarjeta_bancaria", "fecha_transaccion", "valor"]

    # Validar campos requeridos
    for field in required_fields:
        if field not in request.data or not request.data[field]:
            return Response({"error": f"El campo '{field}' es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)

    # Validar existencia de la tarjeta bancaria
    try:
        tarjeta = RegistroTarjetas.objects.get(pk=request.data["id_tarjeta_bancaria"])
    except RegistroTarjetas.DoesNotExist:
        return Response({"error": "La tarjeta bancaria proporcionada no existe."}, status=status.HTTP_400_BAD_REQUEST)

    # Validar que la fecha no sea futura
    from datetime import date
    fecha_transaccion = request.data.get("fecha_transaccion")
    if date.fromisoformat(fecha_transaccion) > date.today():
        return Response({"error": "La fecha de transacción no puede ser en el futuro."}, status=status.HTTP_400_BAD_REQUEST)

    # --- Procesar valor ---
    valor_str = request.data["valor"]

    # Permitir el signo negativo y eliminar puntos
    valor_str = valor_str.replace(".", "")
    try:
        valor = int(valor_str)
    except ValueError:
        return Response({"error": "El valor debe ser un número válido."}, status=status.HTTP_400_BAD_REQUEST)

    # Calcular 4x1000 sólo sobre el valor absoluto
    if tarjeta.is_daviplata:
        cuatro_por_mil = 0
    else:
        cuatro_por_mil = 0 #int(abs(valor) * 0.004)

    # Crear registro
    recepcion_gasto_general = Utilidadocacional.objects.create(
        id_tarjeta_bancaria = tarjeta,
        fecha_transaccion   = fecha_transaccion,
        valor               = valor,  # aquí se guarda el valor negativo o positivo
        cuatro_por_mil      = cuatro_por_mil,
        observacion         = request.data.get("observacion", "")
    )

    serializer = UtilidadocacionalSerializer(recepcion_gasto_general)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

#Obtener una recepción de pago por ID
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1,2)
def obtener_utilidad_general(request, pk):
    try:
        recepcion = Utilidadocacional.objects.get(pk=pk)
    except Utilidadocacional.DoesNotExist:
        return Response({"error": "Recepción de utilidad ocacional no encontrada."}, status=status.HTTP_404_NOT_FOUND)
    
    recepcion.valor = f"{abs(int(recepcion.valor)):,}".replace(",", ".")
    serializer = UtilidadocacionalSerializer(recepcion)
    return Response(serializer.data, status=status.HTTP_200_OK)

#Actualizar una recepción de pago
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@check_role(1,2)
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

    valor = request.data.get("valor",recepcion.valor)  # Obtener el valor del request o mantener el actual
    if isinstance(valor, str):                          # Si el valor es una cadena, limpiarlo
        valor = int(valor.replace(".", ""))             # Eliminar separadores de miles y convertir a número
    
    recepcion.valor =  abs(valor)                       # Asegurar que siempre sea negativo
    recepcion.observacion = request.data.get("observacion", recepcion.observacion)

    if tarjeta.is_daviplata:
        recepcion.cuatro_por_mil = 0
    else:
        recepcion.cuatro_por_mil = int(abs(valor) * 0.004)
        
    recepcion.save()

    serializer = UtilidadocacionalSerializer(recepcion)
    return Response(serializer.data, status=status.HTTP_200_OK)

#Eliminar una recepción de pago
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@check_role(1,2)
def eliminar_utilidad_general(request, pk):
    try:
        recepcion = Utilidadocacional.objects.get(pk=pk)
        recepcion.delete()
        return Response({"mensaje": "Recepción de Utilidad ocacional eliminada correctamente."}, status=status.HTTP_204_NO_CONTENT)
    except Utilidadocacional.DoesNotExist:
        return Response({"error": "Recepción de Utilidad ocacional no encontrada."}, status=status.HTTP_404_NOT_FOUND)
    
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
def obtener_cutilidad_general_filtradas(request):

    fecha_inicio = parse_date_with_defaults(request.GET.get('fechaInicio'))
    fecha_fin    = parse_date_with_defaults(request.GET.get('fechaFin'), is_end=True)

    filtro_fecha = Q()
    if fecha_inicio and fecha_fin:
        filtro_fecha = Q(fecha_ingreso__range=[fecha_inicio, fecha_fin])
    elif fecha_inicio:
        filtro_fecha = Q(fecha_ingreso__gte=fecha_inicio)
    elif fecha_fin:
        filtro_fecha = Q(fecha_ingreso__lte=fecha_fin)

    try:
        utilidades = Utilidadocacional.objects.filter(filtro_fecha)
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
        
                cuatro_por_mil = utilidad.cuatro_por_mil
                if not cuatro_por_mil:
                    cuatro_por_mil = 0

                utilidad_data['total'] = abs(int(utilidad.valor)) - abs(int(cuatro_por_mil))

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



