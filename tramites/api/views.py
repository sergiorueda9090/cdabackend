from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from whatsapp.utils import enviar_mensaje_whatsapp
from tramites.models import Tramite, LogTramite
from users.models import User
from clientes.models import Cliente
from .serializers import TramiteSerializer, LogTramiteSerializer
from rest_framework.permissions import IsAuthenticated
from django.utils.timezone import now
from datetime import datetime

from users.decorators import check_role

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@check_role(1,2,3)
def create_tramite(request):
    # Hacer una copia mutable de request.data
    data = request.data.copy()

    # Agregar idUsuario desde el token
    data['idUsuario'] = request.user.id

    # Obtener el año actual
    current_year = datetime.now().year
    start_of_year = datetime(current_year, 1, 1)
    end_of_year = datetime(current_year, 12, 31, 23, 59, 59)

    # Validar que la placa no se repita en el año actual
    placa = data.get('placa')
    if Tramite.objects.filter(placa=placa, fechaCreacion__range=(start_of_year, end_of_year)).exists():
        return Response(
            {"error": f"La placa '{placa}' ya ha sido registrada este año.", "status":500},
            status=status.HTTP_200_OK
        )

    # Crear el trámite si la placa es válida
    serializer = TramiteSerializer(data=data)
    if serializer.is_valid():
        tramite = serializer.save()
        LogTramite.objects.create(
            idUsuario=request.user.id,  # Obtener el id del usuario autenticado
            idCliente=data.get('idCliente'),
            accion='crear',
            antiguoValor='',
            nuevoValor=str(serializer.data),
            idTramite= tramite.id
        )
        # Incluir el idTramite en la respuesta
        response_data = serializer.data
        response_data['idTramite'] = tramite.id

        return Response(response_data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1,2,3)
def get_tramites(request):
    # Obtener todos los trámites
    tramites = Tramite.objects.all()
    tramites_data = []

    # Procesar cada trámite
    for tramite in tramites:
        print(tramite.idUsuario)
        # Obtener el usuario relacionado
        usuario = get_object_or_404(User, id=tramite.idUsuario)
        
        # Obtener la URL de la imagen del usuario si existe
        imagen_url = usuario.image.url if usuario.image else None

        # Obtener el cliente relacionado
        cliente = get_object_or_404(Cliente, id=tramite.idCliente)

        # Serializar el trámite
        tramite_serializer = TramiteSerializer(tramite)

        # Agregar información del cliente y usuario al trámite
        tramite_data = tramite_serializer.data
        tramite_data['nombre_usuario'] = usuario.username
        tramite_data['image_usuario']  = imagen_url  # Ahora es una URL o None
        tramite_data['nombre_cliente'] = cliente.nombre

        # Añadir al listado de datos
        tramites_data.append(tramite_data)

    return Response(tramites_data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1,2,3)
def get_tramite(request, pk):
    try:
        tramite = Tramite.objects.get(pk=pk)
    except Tramite.DoesNotExist:
        return Response({'error': 'Tramite not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = TramiteSerializer(tramite)
    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@check_role(1,2,3)
def update_tramite(request, pk):
    try:
        tramite = Tramite.objects.get(pk=pk)
    except Tramite.DoesNotExist:
        return Response({'error': 'Trámite no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    # Guardar datos anteriores para el registro del log
    old_data = TramiteSerializer(tramite).data

    # Crear serializador con partial=True para permitir campos opcionales
    serializer = TramiteSerializer(tramite, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        new_data = serializer.data

        # Comparar old_data y new_data para registrar cambios en LogTramite
        for field, old_value in old_data.items():
            new_value = new_data.get(field)
            if old_value != new_value:  # Verificar si hubo un cambio
                LogTramite.objects.create(
                    idTramite=pk,
                    idUsuario=request.data.get('idUsuario', tramite.idUsuario),  # Usar el valor existente si no se envía
                    idCliente=request.data.get('idCliente', tramite.idCliente),  # Igual que arriba
                    accion='editar',
                    campo=field,
                    antiguoValor=str(old_value),
                    nuevoValor=str(new_value),
                    fecha=now()
                )

        archivo_pdf = request.FILES.get('pdf')
        if archivo_pdf and archivo_pdf.content_type == "application/pdf":
            # Mensaje de WhatsApp con enlace al PDF
            telefono = "573104131542"  # Número de teléfono destinatario
            id_tramite = "100000"
            mensaje = f"Hola, se ha generado un trámite con el ID {id_tramite}. Aquí tienes el documento PDF adjunto "

            # Enviar mensaje de WhatsApp
            resultado = enviar_mensaje_whatsapp(telefono, mensaje)

        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@check_role(1,2,3)
def delete_tramite(request, pk):
    try:
        tramite = Tramite.objects.get(pk=pk)
    except Tramite.DoesNotExist:
        return Response({'error': 'Tramite not found'}, status=status.HTTP_404_NOT_FOUND)

    old_data = TramiteSerializer(tramite).data
    tramite.delete()
    LogTramite.objects.create(
        idUsuario=request.data.get('idUsuario'),
        idCliente=request.data.get('idCliente'),
        accion='eliminar',
        antiguoValor=str(old_data),
        nuevoValor='',
    )
    return Response({'message': 'Tramite deleted'}, status=status.HTTP_200_OK)




"""
    LOGS_TRAMITES
"""
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1,2,3)
def get_logs_tramite(request, pk):
    """
    Obtiene todos los registros de LogTramite con el idTramite especificado.
    """
    try:
        # Filtrar todos los registros que tengan idTramite = pk
        tramites = LogTramite.objects.filter(idTramite=pk)
        
        # Si no hay registros, devolver un error 404
        if not tramites.exists():
            return Response({'error': 'No se encontraron logs para este idTramite.'}, status=status.HTTP_404_NOT_FOUND)
        
        # Serializar los datos
        serializer = LogTramiteSerializer(tramites, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)