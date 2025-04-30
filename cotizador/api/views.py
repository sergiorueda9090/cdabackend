from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils.dateparse import parse_date
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils.timezone import now
from datetime import datetime

from users.models               import User
from clientes.models            import Cliente
from etiquetas.models           import Etiqueta
from cotizador.models           import Cotizador, LogCotizador
from cuentasbancarias.models    import CuentaBancaria
from proveedores.models         import Proveedor

from .serializers import CotizadorSerializer, LogCotizadorSerializer
from fichaproveedor.api.serializers import FichaProveedorSerializer
from fichaproveedor.models import FichaProveedor

from users.decorators import check_role

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@check_role(1,2,3)
def create_cotizador(request):
    data = request.data.copy()
    data['idUsuario'] = request.user.id
    data['cotizadorModulo'] = 1

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
@check_role(1,2,3)
def get_cotizadores(request):
    cotizadores = Cotizador.objects.filter(Q(cotizadorModulo=1)).all()
    cotizadores_data = []

    for cotizador in cotizadores:
        usuario = get_object_or_404(User,    id = cotizador.idUsuario)
        
        # Obtener la URL de la imagen del usuario si existe
        imagen_url = usuario.image.url if usuario.image else None

        cliente  = get_object_or_404(Cliente,  id = cotizador.idCliente)
        etiqueta = get_object_or_404(Etiqueta, id = cotizador.idEtiqueta)
        
        cotizador_serializer = CotizadorSerializer(cotizador)

        cotizador_data = cotizador_serializer.data
        cotizador_data['nombre_usuario'] = usuario.username
        cotizador_data['image_usuario']  = imagen_url
        cotizador_data['nombre_cliente'] = cliente.nombre
        cotizador_data['color_cliente']  = cliente.color
        cotizador_data['color_etiqueta'] = etiqueta.color

        cotizadores_data.append(cotizador_data)

    return Response(cotizadores_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1,2,3)
def get_cotizador(request, pk):
    try:
        cotizador = Cotizador.objects.get(pk=pk)
    except Cotizador.DoesNotExist:
        return Response({'error': 'Cotizador no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    serializer = CotizadorSerializer(cotizador)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1,2,3)
def get_cotizadores_filter_date(request):
    # Obtener los parámetros de fecha de la URL
    fecha_inicio = request.GET.get('fechaInicio')
    fecha_fin = request.GET.get('fechaFin')

    # Convertir las fechas a objetos de Python
    fecha_inicio = parse_date(fecha_inicio) if fecha_inicio else None
    fecha_fin = parse_date(fecha_fin) if fecha_fin else None

    # Filtrar los cotizadores
    cotizadores = Cotizador.objects.all()

    if fecha_inicio and fecha_fin:
        cotizadores = cotizadores.filter(fechaCreacion__range=[fecha_inicio, fecha_fin])
    elif fecha_inicio:
        cotizadores = cotizadores.filter(fechaCreacion__gte=fecha_inicio)
    elif fecha_fin:
        cotizadores = cotizadores.filter(fechaCreacion__lte=fecha_fin)

    cotizadores_data = []

    for cotizador in cotizadores:
        usuario = get_object_or_404(User, id=cotizador.idUsuario)
        imagen_url = usuario.image.url if usuario.image else None

        cliente = get_object_or_404(Cliente, id=cotizador.idCliente)
        cotizador_serializer = CotizadorSerializer(cotizador)

        cotizador_data = cotizador_serializer.data
        cotizador_data['nombre_usuario'] = usuario.username
        cotizador_data['image_usuario'] = imagen_url
        cotizador_data['nombre_cliente'] = cliente.nombre

        cotizadores_data.append(cotizador_data)

    return Response(cotizadores_data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1,2,3)
def search_cotizadores(request):
    query = request.GET.get('q', '').strip()  # Limpiar espacios en la búsqueda
    # Consulta normal sin select_related
    if query:
        clientes_ids = Cliente.objects.filter(nombre__icontains=query).values_list('id', flat=True)
        etiqueta_ids = Etiqueta.objects.filter(nombre__icontains=query).values_list('id', flat=True)

        cotizadores = Cotizador.objects.filter(
            Q(placa__icontains=query) | 
            Q(nombreCompleto__icontains=query) | 
            Q(numeroDocumento__icontains=query) |
            Q(tipoDocumento__icontains=query) |
            Q(telefono__icontains=query) |
            Q(correo__icontains=query) |
            Q(etiquetaDos__icontains=query) |
            Q(pagoInmediato__icontains=query) |
            Q(linkPago__icontains=query) |
            Q(precioDeLey__icontains=query) |
            Q(comisionPrecioLey__icontains=query) |
            Q(total__icontains=query) |
            Q(idCliente__in=clientes_ids) |
            Q(idEtiqueta__in=etiqueta_ids)
        )
    else:
        cotizadores = Cotizador.objects.all()

    cotizadores_data = []

    for cotizador in cotizadores:
        # Obtener usuario y cliente sin usar select_related
        usuario = User.objects.filter(id=cotizador.idUsuario).first()
        cliente = Cliente.objects.filter(id=cotizador.idCliente).first()

        cotizador_data = CotizadorSerializer(cotizador).data
        cotizador_data['nombre_usuario'] = usuario.username if usuario else "Desconocido"
        cotizador_data['image_usuario'] = usuario.image.url if usuario and usuario.image else None
        cotizador_data['nombre_cliente'] = cliente.nombre if cliente else "Desconocido"

        cotizadores_data.append(cotizador_data)

    return Response(cotizadores_data)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@check_role(1,2,3)
def update_cotizador(request, pk):
    try:
        cotizador = Cotizador.objects.get(pk=pk)
    except Cotizador.DoesNotExist:
        return Response({'error': 'Cotizador no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    old_data = CotizadorSerializer(cotizador).data

    serializer = CotizadorSerializer(cotizador, data=request.data, partial=True)
    if serializer.is_valid():
        print("Is valid 1")
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

        #AGREGAR REGISTRO EN FICHA PROVEEDOR
        try:
            confirmacionPreciosModulo   = int(request.data.get('confirmacionPreciosModulo') or 0)
            pdfsModulo                  = int(request.data.get('pdfsModulo') or 0)
        except ValueError:
            confirmacionPreciosModulo = 0
            pdfsModulo = 0
        
        if int(confirmacionPreciosModulo) == 0 and int(pdfsModulo) == 1:
            print("=== if ===")
            id_proveedor = request.data.get('idProveedor')
            if not id_proveedor:
                return Response({'error': 'El idProveedor es obligatorio para crear una ficha de proveedor.'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                proveedor = Proveedor.objects.get(pk=id_proveedor)
            except Proveedor.DoesNotExist:
                return Response({'error': 'Proveedor no encontrado'}, status=status.HTTP_404_NOT_FOUND)
            
            comision = request.data.get('comisionproveedor', '0').replace('.', '')  # Elimina separador de miles

            # Crear registro directamente en la base de datos
            ficha = FichaProveedor.objects.create(
                idproveedor=proveedor,
                idcotizador=cotizador,
                comisionproveedor=comision
            )
            print(f"=== Ficha creada con ID {ficha.id} ===")
            #END AGREGAR REGISTRO EN FICHA PROVEEDOR

        id_banco = request.data.get('idBanco')
        
        if id_banco:
            precioDeLey = cotizador.precioDeLey
            precioDeLey = int(precioDeLey.replace(".", ""))
            precioDeLey = -abs(precioDeLey)
            CuentaBancaria.objects.create(
                idCotizador   = cotizador.id, 
                idBanco       = request.data.get('idBanco'),
                descripcion   = "descripcion",
                valor         = precioDeLey,
                cilindraje    = cotizador.cilindraje,
                nombreTitular = cotizador.nombreCompleto)

        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@check_role(1,2,3)
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
@check_role(1,2,3)
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
@check_role(1,2,3)
def get_cotizadores_tramites(request):
    cotizadores = Cotizador.objects.filter(tramiteModulo=1).all()
    
    cotizadores_data = []

    for cotizador in cotizadores:
        usuario = get_object_or_404(User, id = cotizador.idUsuario)
        
        # Obtener la URL de la imagen del usuario si existe
        imagen_url = usuario.image.url if usuario.image else None

        cliente  = get_object_or_404(Cliente, id = cotizador.idCliente)
        etiqueta = get_object_or_404(Etiqueta, id = cotizador.idEtiqueta)
        

        cotizador_serializer = CotizadorSerializer(cotizador)

        cotizador_data = cotizador_serializer.data

        cotizador_data['nombre_usuario'] = usuario.username
        cotizador_data['image_usuario']  = imagen_url
        cotizador_data['nombre_cliente'] = cliente.nombre
        cotizador_data['color_cliente']  = cliente.color
        cotizador_data['color_etiqueta'] = etiqueta.color

        cotizadores_data.append(cotizador_data)

    return Response(cotizadores_data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1,2,3)
def get_cotizadores_confirmacion_precios(request):
    cotizadores = Cotizador.objects.filter(confirmacionPreciosModulo=1).all()
    
    cotizadores_data = []

    for cotizador in cotizadores:
        usuario = get_object_or_404(User, id = cotizador.idUsuario)
        
        # Obtener la URL de la imagen del usuario si existe
        imagen_url = usuario.image.url if usuario.image else None
        
        cliente  = get_object_or_404(Cliente, id = cotizador.idCliente)
        etiqueta = get_object_or_404(Etiqueta, id = cotizador.idEtiqueta)

        cotizador_serializer = CotizadorSerializer(cotizador)

        cotizador_data = cotizador_serializer.data

        cotizador_data['nombre_usuario'] = usuario.username
        cotizador_data['image_usuario']  = imagen_url
        cotizador_data['nombre_cliente'] = cliente.nombre
        cotizador_data['color_cliente']  = cliente.color
        cotizador_data['color_etiqueta'] = etiqueta.color

        cotizadores_data.append(cotizador_data)

    return Response(cotizadores_data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1,2,3)
def get_cotizadores_pdfs(request):
    cotizadores = Cotizador.objects.filter(pdfsModulo=1).all()
    
    cotizadores_data = []

    for cotizador in cotizadores:
        usuario = get_object_or_404(User, id = cotizador.idUsuario)
        
        # Obtener la URL de la imagen del usuario si existe
        imagen_url = usuario.image.url if usuario.image else None
        
        cliente = get_object_or_404(Cliente, id = cotizador.idCliente)
        etiqueta = get_object_or_404(Etiqueta, id = cotizador.idEtiqueta)
        
        cotizador_serializer = CotizadorSerializer(cotizador)

        cotizador_data = cotizador_serializer.data

        cotizador_data['nombre_usuario'] = usuario.username
        cotizador_data['image_usuario']  = imagen_url
        cotizador_data['nombre_cliente'] = cliente.nombre
        cotizador_data['color_cliente']  = cliente.color
        cotizador_data['color_etiqueta'] = etiqueta.color

        cotizadores_data.append(cotizador_data)

    return Response(cotizadores_data)


@api_view(['GET'])
#@permission_classes([IsAuthenticated])
@check_role(1,2,3)
def update_cotizador_to_send_archivo(request):
    print("se ejecuta la tarea programada")
    #return Response({"ok":"ok"})
    try:
        print("SI, se ejecuta la tarea programada")
        # Actualizar los registros con cotizadorModulo=1 y sendToArchivo=0
        updated_rows = Cotizador.objects.filter(cotizadorModulo=1, sendToArchivo=0).update(sendToArchivo=1, cotizadorModulo=0)
        
        return Response({"success": True, "updated_rows": updated_rows})
    
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=500)