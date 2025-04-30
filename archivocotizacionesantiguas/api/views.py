from django.db.models           import Q
from datetime                   import datetime, time
from rest_framework.decorators  import api_view, permission_classes
from django.shortcuts           import get_object_or_404
from rest_framework.response    import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework             import status
from cotizador.api.serializers  import CotizadorSerializer, LogCotizadorSerializer
from cotizador.models           import Cotizador
from users.models               import User
from clientes.models            import Cliente
from etiquetas.models           import Etiqueta
from users.decorators           import check_role

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1,2)
def get_all_cotizadores(request):
    # Obtener parámetros de búsqueda
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin    = request.GET.get('fecha_fin')
    search_query = request.GET.get('search', '')

    # Filtrar por fecha si se proporcionan
    filters = Q()
    if fecha_inicio:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        fecha_inicio = datetime.combine(fecha_inicio, time(0, 0, 0))  # 00:00:00
        filters &= Q(fechaCreacion__gte=fecha_inicio)
    
    if fecha_fin:
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
        fecha_fin = datetime.combine(fecha_fin, time(23, 59, 59))  # 23:59:59
        filters &= Q(fechaCreacion__lte=fecha_fin)

    
    # Búsqueda en todos los campos relevantes
    if search_query:
        filters &= Q(placa__icontains=search_query) | Q(cilindraje__icontains=search_query) | \
                   Q(modelo__icontains=search_query) | Q(chasis__icontains=search_query) | \
                   Q(tipoDocumento__icontains=search_query) | Q(numeroDocumento__icontains=search_query) | \
                   Q(nombreCompleto__icontains=search_query) | Q(telefono__icontains=search_query) | \
                   Q(correo__icontains=search_query) | Q(direccion__icontains=search_query) | \
                   Q(precioDeLey__icontains=search_query) | Q(linkPago__icontains=search_query)
    
    cotizadores = Cotizador.objects.filter(filters).filter(sendToArchivo=1)
    cotizadores_data = []

    for cotizador in cotizadores:
        usuario = get_object_or_404(User, id=cotizador.idUsuario)
        imagen_url = usuario.image.url if usuario.image else None
        cliente = get_object_or_404(Cliente, id=cotizador.idCliente)
        etiqueta = get_object_or_404(Etiqueta, id=cotizador.idEtiqueta)

        cotizador_serializer = CotizadorSerializer(cotizador)
        cotizador_data = cotizador_serializer.data
        cotizador_data['nombre_usuario'] = usuario.username
        cotizador_data['image_usuario'] = imagen_url
        cotizador_data['nombre_cliente'] = cliente.nombre
        cotizador_data['color_cliente'] = cliente.color
        cotizador_data['color_etiqueta'] = etiqueta.color

        cotizadores_data.append(cotizador_data)

    return Response(cotizadores_data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1,2)
def sent_to_tramites(request, idcotizador):
    cotizador = get_object_or_404(Cotizador, id=idcotizador)
    cotizador.tramiteModulo   = 1
    cotizador.sendToArchivo   = 2
    cotizador.save()
    return Response({"message": "Cotizador actualizado exitosamente", "id": idcotizador})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1,2)
def get_cotizador(request, idcotizador):
    # Obtener el cotizador por id
    cotizador = get_object_or_404(Cotizador, id=idcotizador)

    # Obtener el usuario, cliente y etiqueta relacionados
    usuario = get_object_or_404(User, id=cotizador.idUsuario)
    imagen_url = usuario.image.url if usuario.image else None
    cliente = get_object_or_404(Cliente, id=cotizador.idCliente)
    etiqueta = get_object_or_404(Etiqueta, id=cotizador.idEtiqueta)

    # Serializar los datos del cotizador
    cotizador_serializer = CotizadorSerializer(cotizador)
    cotizador_data = cotizador_serializer.data

    # Añadir información adicional al resultado
    cotizador_data['nombre_usuario'] = usuario.username
    cotizador_data['image_usuario'] = imagen_url
    cotizador_data['nombre_cliente'] = cliente.nombre
    cotizador_data['color_cliente'] = cliente.color
    cotizador_data['color_etiqueta'] = etiqueta.color

    return Response(cotizador_data)





