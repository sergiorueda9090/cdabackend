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
from registroTarjetas.models    import RegistroTarjetas

from .serializers import CotizadorSerializer, LogCotizadorSerializer
from fichaproveedor.api.serializers import FichaProveedorSerializer
from fichaproveedor.models import FichaProveedor

from users.decorators import check_role
def agregar_meses(fecha, meses):
    año = fecha.year + (fecha.month + meses - 1) // 12
    mes = (fecha.month + meses - 1) % 12 + 1
    dia = min(fecha.day, [31,
                          29 if año % 4 == 0 and (año % 100 != 0 or año % 400 == 0) else 28,
                          31, 30, 31, 30, 31, 31, 30, 31, 30, 31][mes - 1])
    return datetime(año, mes, dia)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@check_role(1, 2, 3)
def create_cotizador(request):
    data              = request.data.copy()
    data['idUsuario'] = request.user.id
    data['cotizadorModulo'] = 1

    placa = data.get('placa')
    if not placa:
        return Response({"error": "El campo 'placa' es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)

    #Validación: 10 meses desde el último registro
    ultimo_registro = Cotizador.objects.filter(placa=placa).order_by('-fechaCreacion').first()
    if ultimo_registro:
        fecha_limite = agregar_meses(ultimo_registro.fechaCreacion, 10)
        if datetime.now() < fecha_limite:
            return Response(
                {
                    "error": f"La placa '{placa}' ya fue registrada. Deben pasar al menos 10 meses para volver a registrarla.",
                    "status": 500
                },
                status=status.HTTP_200_OK
            )

    #Guardar cotizador
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


# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# @check_role(1, 2, 3)
# def create_cotizador_excel(request):
#     registros = request.data.get("registros", [])

#     if not registros or not isinstance(registros, list):
#         return Response(
#             {"error": "Se esperaba un array de registros"},
#             status=status.HTTP_400_BAD_REQUEST
#         )

#     resultados = []
#     errores = []

#     for idx, registro in enumerate(registros, start=1):

#         print(f"➡️ Procesando registro {idx}: {registro.get('nombre_cliente')}")
        
#         if not registro.get('nombre_cliente'):
#             errores.append({"fila": idx, "error": "El campo 'nombre_cliente' es obligatorio."})
#             continue

#         if not registro.get('nombre_cliente', '').strip():
#             errores.append({"fila": idx, "error": "El campo 'nombre_cliente' no puede estar vacío."})
#             continue

#         if not registro.get('nombre_completo'):
#             errores.append({"fila": idx, "error": "El campo 'nombre_completo' es obligatorio."})
#             continue

#         if not registro.get('nombre_completo', '').strip():
#             errores.append({"fila": idx, "error": "El campo 'nombre_completo' no puede estar vacío."})
#             continue

#         # Buscar cliente por nombre
#         cliente = Cliente.objects.filter(nombre=registro.get('nombre_cliente'))
#         if cliente.exists():
#             registro['idCliente'] = cliente.first().id
#         else:
#             errores.append({"fila": idx, "error": f"Cliente '{registro.get('nombre_cliente')}' no encontrado."})
#             continue

#         # Buscar etiqueta por nombre
#         etiqueta = Etiqueta.objects.filter(nombre=registro.get('etiqueta'))
#         if etiqueta.exists():
#             registro['idEtiqueta'] = etiqueta.first().id
#         else:
#             errores.append({"fila": idx, "error": f"Etiqueta '{registro.get('etiqueta')}' no encontrada."})
#             continue

#         try:
#             data = registro.copy()
#             data['idUsuario'] = request.user.id
#             data['cotizadorModulo'] = 1

#             if 'etiqueta' in data:
#                 data['etiquetaDos'] = data.pop('etiqueta')

#             if 'nombre_completo' in data:
#                 data['nombreCompleto'] = data.pop('nombre_completo')

#             if 'numero_documento' in data:
#                 data['numeroDocumento'] = data.pop('numero_documento')

#             if 'tipo_documento' in data:
#                 data['tipoDocumento'] = data.pop('tipo_documento')
            
#             placa = data.get('placa')
#             if not placa:
#                 errores.append({"fila": idx, "error": "El campo 'placa' es obligatorio."})
#                 continue

#             # ✅ Validación: 10 meses desde el último registro
#             ultimo_registro = Cotizador.objects.filter(placa=placa).order_by('-fechaCreacion').first()
#             if ultimo_registro:
#                 fecha_limite = agregar_meses(ultimo_registro.fechaCreacion, 10)
#                 if datetime.now() < fecha_limite:
#                     errores.append({
#                         "fila": idx,
#                         "error": f"La placa '{placa}' ya fue registrada. Deben pasar al menos 10 meses para volver a registrarla."
#                     })
#                     continue

#             # ✅ Guardar cotizador
#             serializer = CotizadorSerializer(data=data)
#             if serializer.is_valid():
#                 cotizador = serializer.save()
#                 LogCotizador.objects.create(
#                     idUsuario=request.user.id,
#                     idCliente=data.get('idCliente'),
#                     accion='crear',
#                     antiguoValor='',
#                     nuevoValor=str(serializer.data),
#                     idCotizador=cotizador.id
#                 )
#                 resultado = serializer.data
#                 resultado['idCotizador'] = cotizador.id
#                 resultados.append(resultado)
#             else:
#                 errores.append({"fila": idx, "error": serializer.errors})

#         except Exception as e:
#             print("❌ Error en el backend:", str(e))
#             errores.append({"fila": idx, "error": str(e)})

#     if errores:
#         return Response(
#             {"success": False, "guardados": resultados, "errores": errores},
#             status=status.HTTP_207_MULTI_STATUS  # ⚡ respuesta mixta
#         )

#     return Response(
#         {"success": True, "guardados": resultados},
#         status=status.HTTP_201_CREATED
#     )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@check_role(1, 2, 3)
def create_cotizador_excel(request):
    registros = request.data.get("registros", [])

    if not registros or not isinstance(registros, list):
        return Response(
            {"error": "Se esperaba un array de registros"},
            status=status.HTTP_400_BAD_REQUEST
        )

    resultados = []
    errores = []

    for idx, registro in enumerate(registros, start=1):

        print(f"➡️ Procesando registro {idx}: {registro.get('nombre_cliente')}")

        # Validaciones básicas
        if not registro.get('nombre_cliente'):
            errores.append({"fila": idx, "error": "El campo 'nombre_cliente' es obligatorio."})
            continue

        if not registro.get('nombre_cliente', '').strip():
            errores.append({"fila": idx, "error": "El campo 'nombre_cliente' no puede estar vacío."})
            continue

        if not registro.get('nombre_completo'):
            errores.append({"fila": idx, "error": "El campo 'nombre_completo' es obligatorio."})
            continue

        if not registro.get('nombre_completo', '').strip():
            errores.append({"fila": idx, "error": "El campo 'nombre_completo' no puede estar vacío."})
            continue

        #Buscar cliente por nombre
        cliente = Cliente.objects.filter(nombre=registro.get('nombre_cliente'))
        if cliente.exists():
            registro['idCliente'] = cliente.first().id
        else:
            errores.append({"fila": idx, "error": f"Cliente '{registro.get('nombre_cliente')}' no encontrado."})
            continue

        #Buscar etiqueta por nombre
        etiqueta = Etiqueta.objects.filter(nombre=registro.get('etiqueta'))
        if etiqueta.exists():
            registro['idEtiqueta'] = etiqueta.first().id
        else:
            errores.append({"fila": idx, "error": f"Etiqueta '{registro.get('etiqueta')}' no encontrada."})
            continue

        try:
            data = registro.copy()
            data['idUsuario'] = request.user.id
            data['cotizadorModulo'] = 1

            if 'etiqueta' in data:
                data['etiquetaDos'] = data.pop('etiqueta')

            if 'nombre_completo' in data:
                data['nombreCompleto'] = data.pop('nombre_completo')

            if 'numero_documento' in data:
                data['numeroDocumento'] = data.pop('numero_documento')

            if 'tipo_documento' in data:
                data['tipoDocumento'] = data.pop('tipo_documento')

            # ✅ Nuevo: incluir teléfono si existe
            if 'telefono' in data:
                telefono = str(data.pop('telefono')).strip()
                if telefono:
                    data['telefono'] = telefono

            placa = data.get('placa')
            if not placa:
                errores.append({"fila": idx, "error": "El campo 'placa' es obligatorio."})
                continue

            # ✅ Validar antigüedad de la placa (mínimo 10 meses)
            ultimo_registro = Cotizador.objects.filter(placa=placa).order_by('-fechaCreacion').first()
            if ultimo_registro:
                fecha_limite = agregar_meses(ultimo_registro.fechaCreacion, 10)
                if datetime.now() < fecha_limite:
                    errores.append({
                        "fila": idx,
                        "error": f"La placa '{placa}' ya fue registrada. Deben pasar al menos 10 meses para volver a registrarla."
                    })
                    continue

            # ✅ Guardar el cotizador
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
                resultado = serializer.data
                resultado['idCotizador'] = cotizador.id
                resultados.append(resultado)
            else:
                errores.append({"fila": idx, "error": serializer.errors})

        except Exception as e:
            print("❌ Error en el backend:", str(e))
            errores.append({"fila": idx, "error": str(e)})

    if errores:
        return Response(
            {"success": False, "guardados": resultados, "errores": errores},
            status=status.HTTP_207_MULTI_STATUS
        )

    return Response(
        {"success": True, "guardados": resultados},
        status=status.HTTP_201_CREATED
    )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@check_role(1, 2, 3)
def create_cotizador_tramites_excel(request):
    registros = request.data.get("registros", [])

    if not registros or not isinstance(registros, list):
        return Response(
            {"error": "Se esperaba un array de registros"},
            status=status.HTTP_400_BAD_REQUEST
        )

    resultados = []
    errores = []

    for idx, registro in enumerate(registros, start=1):

        print(f"➡️ Procesando registro {idx}: {registro.get('nombre_cliente')}")

        # Validaciones básicas
        if not registro.get('nombre_cliente'):
            errores.append({"fila": idx, "error": "El campo 'nombre_cliente' es obligatorio."})
            continue

        if not registro.get('nombre_cliente', '').strip():
            errores.append({"fila": idx, "error": "El campo 'nombre_cliente' no puede estar vacío."})
            continue

        if not registro.get('nombre_completo'):
            errores.append({"fila": idx, "error": "El campo 'nombre_completo' es obligatorio."})
            continue

        if not registro.get('nombre_completo', '').strip():
            errores.append({"fila": idx, "error": "El campo 'nombre_completo' no puede estar vacío."})
            continue

        #Buscar cliente por nombre
        cliente = Cliente.objects.filter(nombre=registro.get('nombre_cliente'))
        if cliente.exists():
            registro['idCliente'] = cliente.first().id
        else:
            errores.append({"fila": idx, "error": f"Cliente '{registro.get('nombre_cliente')}' no encontrado."})
            continue

        #Buscar etiqueta por nombre
        etiqueta = Etiqueta.objects.filter(nombre=registro.get('etiqueta'))
        if etiqueta.exists():
            registro['idEtiqueta'] = etiqueta.first().id
        else:
            errores.append({"fila": idx, "error": f"Etiqueta '{registro.get('etiqueta')}' no encontrada."})
            continue

        try:
            data = registro.copy()
            data['idUsuario'] = request.user.id
            data['tramiteModulo'] = 1
            data['confirmacionPreciosModulo'] = 0
            data['cotizadorModulo'] = 0
            data['pdfsModulo'] = 0

            if 'etiqueta' in data:
                data['etiquetaDos'] = data.pop('etiqueta')

            if 'nombre_completo' in data:
                data['nombreCompleto'] = data.pop('nombre_completo')

            if 'numero_documento' in data:
                data['numeroDocumento'] = data.pop('numero_documento')

            if 'tipo_documento' in data:
                data['tipoDocumento'] = data.pop('tipo_documento')

            # ✅ Nuevo: incluir teléfono si existe
            if 'telefono' in data:
                telefono = str(data.pop('telefono')).strip()
                if telefono:
                    data['telefono'] = telefono

            placa = data.get('placa')
            if not placa:
                errores.append({"fila": idx, "error": "El campo 'placa' es obligatorio."})
                continue

            # ✅ Validar antigüedad de la placa (mínimo 10 meses)
            ultimo_registro = Cotizador.objects.filter(placa=placa).order_by('-fechaCreacion').first()
            if ultimo_registro:
                fecha_limite = agregar_meses(ultimo_registro.fechaCreacion, 10)
                if datetime.now() < fecha_limite:
                    errores.append({
                        "fila": idx,
                        "error": f"La placa '{placa}' ya fue registrada. Deben pasar al menos 10 meses para volver a registrarla."
                    })
                    continue

            # ✅ Guardar el cotizador
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
                resultado = serializer.data
                resultado['idCotizador'] = cotizador.id
                resultados.append(resultado)
            else:
                errores.append({"fila": idx, "error": serializer.errors})

        except Exception as e:
            print("❌ Error en el backend:", str(e))
            errores.append({"fila": idx, "error": str(e)})

    if errores:
        return Response(
            {"success": False, "guardados": resultados, "errores": errores},
            status=status.HTTP_207_MULTI_STATUS
        )

    return Response(
        {"success": True, "guardados": resultados},
        status=status.HTTP_201_CREATED
    )

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
    fecha_fin    = request.GET.get('fechaFin')

    # Convertir las fechas a objetos de Python
    fecha_inicio = parse_date(fecha_inicio) if fecha_inicio else None
    fecha_fin    = parse_date(fecha_fin) if fecha_fin else None

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

        etiqueta = get_object_or_404(Etiqueta, id = cotizador.idEtiqueta)
        
        cotizador_data = cotizador_serializer.data
        cotizador_data['nombre_usuario']  = usuario.username
        cotizador_data['image_usuario']   = imagen_url
        cotizador_data['nombre_cliente']  = cliente.nombre
        cotizador_data['color_cliente']   = cliente.color
        cotizador_data['color_etiqueta']  = etiqueta.color

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
    print(" =================== INGRESA =================")
    try:
        cotizador = Cotizador.objects.get(pk=pk)
    except Cotizador.DoesNotExist:
        return Response({'error': 'Cotizador no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    id_banco = request.data.get('idBanco')

    tramite_modulo              = int(request.data.get('tramiteModulo') or 1)
    confirmacion_precios_modulo = int(request.data.get('confirmacionPreciosModulo') or 1)

    if tramite_modulo != 1:
        if confirmacion_precios_modulo != 1:
            if id_banco:
                # Validar que precioDeLey tenga un valor no vacío y no nulo
                precio_de_ley_raw = cotizador.precioDeLey
                if not precio_de_ley_raw:
                    return Response(
                        {'error': 'El campo precio De Ley es obligatorio si se proporciona un una tarjeta.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
            if not cotizador.precioDeLey:
                precio_de_ley_raw = cotizador.precioDeLey
                if not precio_de_ley_raw:
                    return Response(
                        {'error': 'El campo precio De Ley es obligatorio si se proporciona un una tarjeta.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

    
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

        #AGREGAR REGISTRO EN FICHA PROVEEDOR
        try:
            confirmacionPreciosModulo   = int(request.data.get('confirmacionPreciosModulo') or 0)
            pdfsModulo                  = int(request.data.get('pdfsModulo') or 0)
        except ValueError:
            confirmacionPreciosModulo = 0
            pdfsModulo = 0
        
        if int(confirmacionPreciosModulo) == 0 and int(pdfsModulo) == 1:
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
            """precioDeLey = cotizador.precioDeLey
            precioDeLey = int(precioDeLey.replace(".", ""))
            precioDeLey = -abs(precioDeLey)"""
            
            precioDeLey = cotizador.precioDeLey
            precioDeLey = int(precioDeLey.replace(".", ""))
            precioDeLey = -abs(precioDeLey)

            # Obtener banco y verificar si es Daviplata
            registro_tarjeta = RegistroTarjetas.objects.get(id=id_banco)

            if registro_tarjeta.is_daviplata:
                cuatro_por_mil = 0
            else:
                cuatro_por_mil = int(abs(precioDeLey) * 0.004)

            # Mostrar el resultado (opcional)
            CuentaBancaria.objects.create(
                idCotizador   = cotizador.id, 
                idBanco       = request.data.get('idBanco'),
                descripcion   = "descripcion",
                valor         = precioDeLey,
                cuatro_por_mil= cuatro_por_mil,
                cilindraje    = cotizador.cilindraje,
                nombreTitular = cotizador.nombreCompleto)

        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@check_role(1, 2, 3)
def update_cotizador_pdf(request, pk):
    from whatsapp.utils import enviar_documento_whatsapp, send_email

    try:
        cotizador = Cotizador.objects.get(pk=pk)
    except Cotizador.DoesNotExist:
        return Response({'error': 'Cotizador no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    try:
        cliente = Cliente.objects.filter(id=cotizador.idCliente).values_list('telefono','email','medio_contacto').first()
    except Cotizador.DoesNotExist:
        return Response({'error': 'El cliente no tiene un número telefónico para enviar el WhatsApp'}, status=status.HTTP_404_NOT_FOUND)
    
    if not cliente:
        return Response(
            {'error': 'El cliente no tiene un número telefónico para enviar el WhatsApp'},
            status=status.HTTP_404_NOT_FOUND
        )

    placa = cotizador.placa
    telefono, email, medio_contacto = cliente

    old_archivo = cotizador.archivo  # guarda el valor anterior

    # Solo permitimos actualizar el campo 'archivo'
    data = {
        'pdf': request.data.get('pdf'),
        'pdfsModulo': '0'
    }

    serializer = CotizadorSerializer(cotizador, data=data, partial=True)
    if serializer.is_valid():
        serializer.save()
        
        Cotizador.objects.filter(pk=pk).update(pdfsModulo='0')

        new_archivo = serializer.validated_data.get('archivo')
        new_pdf     = Cotizador.objects.get(pk=pk).pdf.url if Cotizador.objects.get(pk=pk).pdf else None
   
        if old_archivo != new_archivo:
            LogCotizador.objects.create(
                idCotizador=pk,
                idUsuario=request.data.get('idUsuario', cotizador.idUsuario),
                idCliente=request.data.get('idCliente', cotizador.idCliente),
                accion='editar',
                campo='archivo',
                antiguoValor=str(old_archivo),
                nuevoValor=str(new_archivo),
                fecha=now()
            )

        #Envío del WhatsApp con el nuevo documento
        print("==== medio_contacto ==== ",medio_contacto)
        if medio_contacto == "whatsapp":
            if telefono and new_pdf:
                #link_documento = 'https://backend.movilidad2a.com/media/'+new_pdf
                link_documento = new_pdf
                print("Link del documento:", link_documento)
                telefono = telefono #"573143801560"#"573104131542"
                print(" == NUMERO TELEFONO === ", telefono)
                resultado = enviar_documento_whatsapp(telefono=telefono, link_documento=link_documento, numero_soat=placa)
                print("Resultado WhatsApp:", resultado)
        else:
            #link_documento = 'https://backend.movilidad2a.com/media/'+new_pdf
            #link_documento = 'http://127.0.0.1:8000/media/'+new_pdf
            link_documento = new_pdf
            print("email ",email)
            print("link_documento ",link_documento)
            send_email(email, pdf_url=link_documento, placa_te=placa)

        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@check_role(1, 2, 3)
def delete_cotizador(request, pk):
    try:
        cotizador = Cotizador.objects.get(pk=pk)
    except Cotizador.DoesNotExist:
        return Response({'error': 'Cotizador no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    old_data = CotizadorSerializer(cotizador).data

    LogCotizador.objects.create(
        idUsuario=request.user.id,  # <-- Usa el usuario autenticado
        idCliente=cotizador.idCliente,  # <-- Puedes obtenerlo directamente del modelo
        idCotizador=cotizador.id,
        accion='eliminar',
        antiguoValor=str(old_data),
        nuevoValor='',
    )

    cotizador.delete()

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
def get_cotizadores_confirmacion_precios_id(request, pk):
    cotizador = Cotizador.objects.filter(confirmacionPreciosModulo=1, id=pk).first()
    if not cotizador:
        return Response({"error": "Cotizador no encontrado"}, status=404)

    usuario = get_object_or_404(User, id=cotizador.idUsuario)
    imagen_url = usuario.image.url if usuario.image else None
    cliente = get_object_or_404(Cliente, id=cotizador.idCliente)
    etiqueta = get_object_or_404(Etiqueta, id=cotizador.idEtiqueta)

    cotizador_serializer = CotizadorSerializer(cotizador)
    cotizador_data = cotizador_serializer.data

    cotizador_data['nombre_usuario'] = usuario.username
    cotizador_data['image_usuario']  = imagen_url
    cotizador_data['nombre_cliente'] = cliente.nombre
    cotizador_data['color_cliente']  = cliente.color
    cotizador_data['color_etiqueta'] = etiqueta.color
    print(cotizador_data)
    return Response(cotizador_data)


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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1, 2, 3)
def get_cotizadores_trasabilidad_filter_date(request):
    # Filtros de fecha
    fecha_inicio = request.GET.get('fechaInicio')
    fecha_fin    = request.GET.get('fechaFin')
    query        = request.GET.get('q', '').strip()

    fecha_inicio = parse_date(fecha_inicio) if fecha_inicio else None
    fecha_fin    = parse_date(fecha_fin) if fecha_fin else None

    # Filtro base
    cotizadores = Cotizador.objects.filter(tramiteModulo=1)

    # Filtro por fecha
    if fecha_inicio and fecha_fin:
        cotizadores = cotizadores.filter(fechaCreacion__range=[fecha_inicio, fecha_fin])
    elif fecha_inicio:
        cotizadores = cotizadores.filter(fechaCreacion__gte=fecha_inicio)
    elif fecha_fin:
        cotizadores = cotizadores.filter(fechaCreacion__lte=fecha_fin)

    # Filtro por búsqueda
    if query:
        clientes_ids = Cliente.objects.filter(nombre__icontains=query).values_list('id', flat=True)
        etiqueta_ids = Etiqueta.objects.filter(nombre__icontains=query).values_list('id', flat=True)

        cotizadores = cotizadores.filter(
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

    cotizadores_data = []

    for cotizador in cotizadores:
        usuario = User.objects.filter(id=cotizador.idUsuario).first()
        cliente = Cliente.objects.filter(id=cotizador.idCliente).first()
        etiqueta = Etiqueta.objects.filter(id=cotizador.idEtiqueta).first()

        cotizador_data = CotizadorSerializer(cotizador).data
        cotizador_data['nombre_usuario']  = usuario.username if usuario else "Desconocido"
        cotizador_data['image_usuario']   = usuario.image.url if usuario and usuario.image else None
        cotizador_data['nombre_cliente']  = cliente.nombre if cliente else "Desconocido"
        cotizador_data['color_cliente']   = cliente.color if cliente else None
        cotizador_data['color_etiqueta']  = etiqueta.color if etiqueta else None

        cotizadores_data.append(cotizador_data)

    return Response(cotizadores_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1, 2, 3)
def get_cotizadores_confirmacion_filter_date(request):
    # Filtros de fecha
    fecha_inicio = request.GET.get('fechaInicio')
    fecha_fin    = request.GET.get('fechaFin')
    query        = request.GET.get('q', '').strip()

    fecha_inicio = parse_date(fecha_inicio) if fecha_inicio else None
    fecha_fin    = parse_date(fecha_fin) if fecha_fin else None

    # Filtro base
    cotizadores = Cotizador.objects.filter(confirmacionPreciosModulo=1)
    
    # Filtro por fecha
    if fecha_inicio and fecha_fin:
        cotizadores = cotizadores.filter(fechaCreacion__range=[fecha_inicio, fecha_fin])
    elif fecha_inicio:
        cotizadores = cotizadores.filter(fechaCreacion__gte=fecha_inicio)
    elif fecha_fin:
        cotizadores = cotizadores.filter(fechaCreacion__lte=fecha_fin)

    # Filtro por búsqueda
    if query:
        clientes_ids = Cliente.objects.filter(nombre__icontains=query).values_list('id', flat=True)
        etiqueta_ids = Etiqueta.objects.filter(nombre__icontains=query).values_list('id', flat=True)

        cotizadores = cotizadores.filter(
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

    cotizadores_data = []

    for cotizador in cotizadores:
        usuario = User.objects.filter(id=cotizador.idUsuario).first()
        cliente = Cliente.objects.filter(id=cotizador.idCliente).first()
        etiqueta = Etiqueta.objects.filter(id=cotizador.idEtiqueta).first()

        cotizador_data = CotizadorSerializer(cotizador).data
        cotizador_data['nombre_usuario']  = usuario.username if usuario else "Desconocido"
        cotizador_data['image_usuario']   = usuario.image.url if usuario and usuario.image else None
        cotizador_data['nombre_cliente']  = cliente.nombre if cliente else "Desconocido"
        cotizador_data['color_cliente']   = cliente.color if cliente else None
        cotizador_data['color_etiqueta']  = etiqueta.color if etiqueta else None

        cotizadores_data.append(cotizador_data)

    return Response(cotizadores_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1, 2, 3)
def get_cotizadores_pdf_filter_date(request):
    # Filtros de fecha
    fecha_inicio = request.GET.get('fechaInicio')
    fecha_fin    = request.GET.get('fechaFin')
    query        = request.GET.get('q', '').strip()

    fecha_inicio = parse_date(fecha_inicio) if fecha_inicio else None
    fecha_fin    = parse_date(fecha_fin) if fecha_fin else None

    # Filtro base
    cotizadores = Cotizador.objects.filter(pdfsModulo=1)
    
    # Filtro por fecha
    if fecha_inicio and fecha_fin:
        cotizadores = cotizadores.filter(fechaCreacion__range=[fecha_inicio, fecha_fin])
    elif fecha_inicio:
        cotizadores = cotizadores.filter(fechaCreacion__gte=fecha_inicio)
    elif fecha_fin:
        cotizadores = cotizadores.filter(fechaCreacion__lte=fecha_fin)

    # Filtro por búsqueda
    if query:
        clientes_ids = Cliente.objects.filter(nombre__icontains=query).values_list('id', flat=True)
        etiqueta_ids = Etiqueta.objects.filter(nombre__icontains=query).values_list('id', flat=True)

        cotizadores = cotizadores.filter(
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

    cotizadores_data = []

    for cotizador in cotizadores:
        usuario = User.objects.filter(id=cotizador.idUsuario).first()
        cliente = Cliente.objects.filter(id=cotizador.idCliente).first()
        etiqueta = Etiqueta.objects.filter(id=cotizador.idEtiqueta).first()

        cotizador_data = CotizadorSerializer(cotizador).data
        cotizador_data['nombre_usuario']  = usuario.username if usuario else "Desconocido"
        cotizador_data['image_usuario']   = usuario.image.url if usuario and usuario.image else None
        cotizador_data['nombre_cliente']  = cliente.nombre if cliente else "Desconocido"
        cotizador_data['color_cliente']   = cliente.color if cliente else None
        cotizador_data['color_etiqueta']  = etiqueta.color if etiqueta else None

        cotizadores_data.append(cotizador_data)

    return Response(cotizadores_data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@check_role(1, 2, 3)
def update_cotizador_devolver(request, pk):
    try:
        cotizador = Cotizador.objects.get(pk=pk)
    except Cotizador.DoesNotExist:
        return Response({'error': 'Cotizador no encontrado'}, status=status.HTTP_404_NOT_FOUND)
    
    devolver = request.data.get('devolver')

    if devolver == "pdf":
        cotizador.confirmacionPreciosModulo = 1
        cotizador.pdf                       = ""
    elif devolver == "confirmarprecio":
        cotizador.confirmacionPreciosModulo = 0
        cotizador.pdfsModulo                = 0
        cotizador.archivo                   = ""
        cotizador.tramiteModulo             = 1
        FichaProveedor.objects.filter(idcotizador=cotizador.id).delete()
        CuentaBancaria.objects.filter(idCotizador=cotizador.id).delete()
    elif devolver == "tramite":
        cotizador.confirmacionPreciosModulo = 0
        cotizador.pdfsModulo                = 0
        cotizador.tramiteModulo             = 0
        cotizador.cotizadorModulo           = 1
    else:
        return Response({'error': 'Valor de "devolver" inválido'}, status=status.HTTP_400_BAD_REQUEST)

    cotizador.save()
    serializer = CotizadorSerializer(cotizador)
    return Response(serializer.data, status=status.HTTP_200_OK)