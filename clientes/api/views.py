from django.http                import JsonResponse
from rest_framework.decorators  import api_view, permission_classes
from rest_framework             import status
from clientes.models            import Cliente, PrecioLey
from generadortoken.models      import GeneradorToken  # Importar el modelo del token
from .serializers               import ClienteSerializer, PrecioLeySerializer
from rest_framework.permissions import IsAuthenticated
import json
import random  # Para generar el token

# Obtener todos los clientes
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_clientes(request):
    if request.method == 'GET':
        clientes = Cliente.objects.all()
        serializer = ClienteSerializer(clientes, many=True)
        return JsonResponse(serializer.data, safe=False, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_clientes_tramites(request):
    clientes = Cliente.objects.all()
    response_data = [
        {"value": cliente.id, "label": f"{cliente.nombre} {cliente.apellidos}"} for cliente in clientes
    ]
    return JsonResponse(response_data, safe=False, status=status.HTTP_200_OK)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_cliente(request):
    if request.method == 'POST':
        # Copiar los datos para modificarlos
        data = request.POST.copy()

        # Validar y deserializar precios_ley si está presente
        precios_ley = data.get('precios_ley', None)
        print(precios_ley)
        if precios_ley:
            try:
                precios_ley = json.loads(precios_ley)
                if not isinstance(precios_ley, list):
                    raise ValueError("El campo precios_ley debe ser una lista de objetos.")
            except (json.JSONDecodeError, ValueError):
                return JsonResponse(
                    {"error": "El campo precios_ley debe ser un JSON válido y contener una lista."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            precios_ley = []

        # Validar los campos obligatorios del cliente
        nombre = data.get('nombre')
        if not nombre or not nombre.strip():
            return JsonResponse({"error": "El campo 'nombre' es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)

        # Campos opcionales
        apellidos = data.get('apellidos', '')
        telefono  = data.get('telefono',  '')
        direccion = data.get('direccion', '')

        # Crear el cliente
        cliente = Cliente.objects.create(
            nombre=nombre.strip(),
            apellidos=apellidos.strip(),
            telefono=telefono.strip(),
            direccion=direccion.strip(),
        )

        # Crear los precios de ley asociados al cliente
        for precio_ley in precios_ley:
            descripcion = precio_ley.get('descripcion')
            precio      = precio_ley.get('precio_ley')
            comision    = precio_ley.get('comision')

            """if not descripcion or not isinstance(precio, (int, float)) or not isinstance(comision, (int, float)):
                return JsonResponse(
                    {"error": "Cada precio de ley debe tener 'descripcion', 'precio_ley' y 'comision' válidos."},
                    status=status.HTTP_400_BAD_REQUEST
                )"""

            PrecioLey.objects.create(
                cliente     = cliente,
                descripcion = descripcion.strip(),
                precio_ley  = precio,
                comision    = comision,
            )

        # Retornar los datos creados
        return JsonResponse({
            "id": cliente.id,
            "nombre": cliente.nombre,
            "apellidos": cliente.apellidos,
            "telefono": cliente.telefono,
            "direccion": cliente.direccion,
            "precios_ley": [
                {
                    "descripcion": p.descripcion,
                    "precio_ley": p.precio_ley,
                    "comision": p.comision
                }
                for p in cliente.precios_ley.all()
            ]
        }, status=status.HTTP_201_CREATED)


# Obtener detalles de un cliente específico
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cliente_detail(request, pk):
    if request.method == 'GET':
        try:
            cliente = Cliente.objects.get(pk=pk)
        except Cliente.DoesNotExist:
            return JsonResponse({'error': 'Cliente no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ClienteSerializer(cliente)
        return JsonResponse(serializer.data, status=status.HTTP_200_OK)


# Actualizar un cliente específico
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_cliente(request, pk):
    if request.method == 'PUT':
        try:
            # Obtener el cliente existente
            cliente = Cliente.objects.get(pk=pk)
        except Cliente.DoesNotExist:
            return JsonResponse({'error': 'Cliente no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        # Copiar los datos del request para manipularlos
        data = request.POST.copy()

        # Procesar precios_ley
        precios_ley = data.get('precios_ley', None)
        if precios_ley:
            try:
                precios_ley = json.loads(precios_ley)
                if not isinstance(precios_ley, list):
                    raise ValueError("El campo precios_ley debe ser una lista de objetos.")
            except (json.JSONDecodeError, ValueError):
                return JsonResponse(
                    {"error": "El campo precios_ley debe ser un JSON válido y contener una lista."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            precios_ley = []

        # Actualizar los datos del cliente
        cliente.nombre      = data.get('nombre', cliente.nombre).strip()
        cliente.apellidos   = data.get('apellidos', cliente.apellidos).strip()
        cliente.telefono    = data.get('telefono', cliente.telefono).strip()
        cliente.direccion   = data.get('direccion', cliente.direccion).strip()
        cliente.save()

        # Obtener los IDs de los precios de ley actuales
        precios_existentes = list(cliente.precios_ley.values_list('id', flat=True))

        # Procesar los precios enviados
        nuevos_precios_ids = []
        for precio in precios_ley:
            precio_id   = precio.get('id', None)
            descripcion = precio.get('descripcion', '').strip()
            precio_ley  = precio.get('precio_ley')
            comision    = precio.get('comision')
            
            """
            if not descripcion or not isinstance(precio_ley, (int, float)) or not isinstance(comision, (int, float)):
                return JsonResponse(
                    {"error": "Cada precio de ley debe tener 'descripcion', 'precioLey' y 'comision' válidos."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            """

            if precio_id and precio_id in precios_existentes:
                # Actualizar un precio existente
                precio_obj = PrecioLey.objects.get(id=precio_id, cliente=cliente)
                precio_obj.descripcion = descripcion
                precio_obj.precio_ley  = precio_ley
                precio_obj.comision    = comision
                precio_obj.save()
                nuevos_precios_ids.append(precio_id)
            else:
                # Crear un nuevo precio
                nuevo_precio = PrecioLey.objects.create(
                    cliente=cliente,
                    descripcion=descripcion,
                    precio_ley=precio_ley,
                    comision=comision
                )
                nuevos_precios_ids.append(nuevo_precio.id)

        # Eliminar los precios de ley no enviados
        precios_a_eliminar = set(precios_existentes) - set(nuevos_precios_ids)
        PrecioLey.objects.filter(id__in=precios_a_eliminar).delete()

        # Respuesta con los datos actualizados
        return JsonResponse({
            "id": cliente.id,
            "nombre": cliente.nombre,
            "apellidos": cliente.apellidos,
            "telefono": cliente.telefono,
            "direccion": cliente.direccion,
            "precios_ley": [
                {
                    "id": p.id,
                    "descripcion": p.descripcion,
                    "precio_ley": p.precio_ley,
                    "comision": p.comision
                }
                for p in cliente.precios_ley.all()
            ]
        }, status=status.HTTP_200_OK)


# Eliminar un cliente específico
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_cliente(request, pk):
    if request.method == 'DELETE':
        try:
            cliente = Cliente.objects.get(pk=pk)
        except Cliente.DoesNotExist:
            return JsonResponse({'error': 'Cliente no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        cliente.delete()
        return JsonResponse({'message': 'Cliente eliminado correctamente'}, status=status.HTTP_204_NO_CONTENT)



@api_view(['POST'])
def verificar_cliente_y_generar_token(request):
    identificacion = request.data.get("identificacion", None)
    if not identificacion:
        return JsonResponse(
            {"error": "El número de identificación es requerido."},status=status.HTTP_201_CREATED
        )
    
    try:
        cliente = Cliente.objects.get(telefono=identificacion)
        token = f"{random.randint(100000, 999999)}"  # Generar un token de 6 dígitos
        
        # Guardar el token en la base de datos
        GeneradorToken.objects.create(
            identificacion=identificacion,
            token=token
        )
        dataCliente = ClienteSerializer(cliente).data
 
        return JsonResponse(
            {
                "message"   : "Cliente encontrado.",
                "id"        : dataCliente['id'],
                "nombre"    : dataCliente['nombre'],
                "apellidos" : dataCliente['apellidos'],
                "token"     : token
            },
            status=status.HTTP_200_OK
        )
    except Cliente.DoesNotExist:
        return JsonResponse(
            {"error": "Cliente no encontrado."},
            status=status.HTTP_201_CREATED
        )