from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils.timezone import now
from datetime import datetime

from users.models import User
from clientes.models import Cliente
from cotizador.models import Cotizador, LogCotizador

from .serializers import CotizadorSerializer, LogCotizadorSerializer

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_cotizador(request):
    data = request.data.copy()
    data['idUsuario'] = request.user.id

    current_year = datetime.now().year
    start_of_year = datetime(current_year, 1, 1)
    end_of_year = datetime(current_year, 12, 31, 23, 59, 59)

    placa = data.get('placa')
    if Cotizador.objects.filter(placa=placa, fechaCreacion__range=(start_of_year, end_of_year)).exists():
        return Response(
            {"error": f"La placa '{placa}' ya ha sido registrada este año.", "status": 500},
            status=status.HTTP_200_OK
        )

    serializer = CotizadorSerializer(data=data)
    if serializer.is_valid():
        cotizador = serializer.save()
        LogCotizador.objects.create(
            idUsuario=request.user.id,
            idCliente=data.get('idCliente'),
            accion='crear',
            antiguoValor='',
            nuevoValor=str(serializer.data),
            idCotizador=cotizador.id
        )
        response_data = serializer.data
        response_data['idCotizador'] = cotizador.id

        return Response(response_data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cotizadores(request):
    cotizadores = Cotizador.objects.all()
    
    cotizadores_data = []

    for cotizador in cotizadores:
        usuario = get_object_or_404(User,    id = cotizador.idUsuario)
        cliente = get_object_or_404(Cliente, id = cotizador.idCliente)

        cotizador_serializer = CotizadorSerializer(cotizador)

        cotizador_data = cotizador_serializer.data
        cotizador_data['nombre_usuario'] = usuario.username
        cotizador_data['nombre_cliente'] = cliente.nombre

        cotizadores_data.append(cotizador_data)

    return Response(cotizadores_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cotizador(request, pk):
    try:
        cotizador = Cotizador.objects.get(pk=pk)
    except Cotizador.DoesNotExist:
        return Response({'error': 'Cotizador no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    serializer = CotizadorSerializer(cotizador)
    return Response(serializer.data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_cotizador(request, pk):
    try:
        cotizador = Cotizador.objects.get(pk=pk)
    except Cotizador.DoesNotExist:
        return Response({'error': 'Cotizador no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    old_data = CotizadorSerializer(cotizador).data

    serializer = CotizadorSerializer(cotizador, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        new_data = serializer.data

        for field, old_value in old_data.items():
            new_value = new_data.get(field)
            if old_value != new_value:
                LogCotizador.objects.create(
                    idCotizador=pk,
                    idUsuario=request.data.get('idUsuario', cotizador.idUsuario),
                    idCliente=request.data.get('idCliente', cotizador.idCliente),
                    accion='editar',
                    campo=field,
                    antiguoValor=str(old_value),
                    nuevoValor=str(new_value),
                    fecha=now()
                )
        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_cotizador(request, pk):
    try:
        cotizador = Cotizador.objects.get(pk=pk)
    except Cotizador.DoesNotExist:
        return Response({'error': 'Cotizador no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    old_data = CotizadorSerializer(cotizador).data
    cotizador.delete()
    LogCotizador.objects.create(
        idUsuario=request.data.get('idUsuario'),
        idCliente=request.data.get('idCliente'),
        accion='eliminar',
        antiguoValor=str(old_data),
        nuevoValor='',
    )
    return Response({'message': 'Cotizador eliminado'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_logs_cotizador(request, pk):
    try:
        logs = LogCotizador.objects.filter(idCotizador=pk)
        if not logs.exists():
            return Response({'error': 'No se encontraron logs para este idCotizador.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = LogCotizadorSerializer(logs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cotizadores_tramites(request):
    cotizadores = Cotizador.objects.filter(tramiteModulo=1).all()
    
    cotizadores_data = []

    for cotizador in cotizadores:
        usuario = get_object_or_404(User, id = cotizador.idUsuario)
        
        # Obtener la URL de la imagen del usuario si existe
        imagen_url = usuario.image.url if usuario.image else None

        cliente = get_object_or_404(Cliente, id = cotizador.idCliente)

        cotizador_serializer = CotizadorSerializer(cotizador)

        cotizador_data = cotizador_serializer.data

        cotizador_data['nombre_usuario'] = usuario.username
        cotizador_data['image_usuario']  = imagen_url
        cotizador_data['nombre_cliente'] = cliente.nombre

        cotizadores_data.append(cotizador_data)

    return Response(cotizadores_data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cotizadores_confirmacion_precios(request):
    cotizadores = Cotizador.objects.filter(confirmacionPreciosModulo=1).all()
    
    cotizadores_data = []

    for cotizador in cotizadores:
        usuario = get_object_or_404(User, id = cotizador.idUsuario)
        
        # Obtener la URL de la imagen del usuario si existe
        imagen_url = usuario.image.url if usuario.image else None

        cliente = get_object_or_404(Cliente, id = cotizador.idCliente)

        cotizador_serializer = CotizadorSerializer(cotizador)

        cotizador_data = cotizador_serializer.data

        cotizador_data['nombre_usuario'] = usuario.username
        cotizador_data['image_usuario']  = imagen_url
        cotizador_data['nombre_cliente'] = cliente.nombre

        cotizadores_data.append(cotizador_data)

    return Response(cotizadores_data)

