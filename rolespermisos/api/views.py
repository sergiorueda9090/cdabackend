from rest_framework             import status
from rest_framework.decorators  import api_view
from rest_framework.response    import Response
from rolespermisos.models       import Rolespermisos
from .seriealizers              import RolespermisosSerializer

# Función para crear un nuevo Rolpermiso
@api_view(['POST'])
def rolespermisos_create(request):
    if request.method == 'POST':
        serializer = RolespermisosSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Función para obtener un Rolpermiso específico
@api_view(['GET'])
def rolespermisos_detail(request, pk):
    try:
        rolpermiso = Rolespermisos.objects.get(pk=pk)
    except Rolespermisos.DoesNotExist:
        return Response({'error': 'Rolpermiso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = RolespermisosSerializer(rolpermiso)
        return Response(serializer.data, status=status.HTTP_200_OK)

# Función para obtener todos los Rolespermisos
@api_view(['GET'])
def rolespermisos_list(request):
    if request.method == 'GET':
        rolpermisos = Rolespermisos.objects.all()
        serializer = RolespermisosSerializer(rolpermisos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

# Función para actualizar un Rolpermiso existente
@api_view(['PUT'])
def rolespermisos_update(request, pk):
    try:
        rolpermiso = Rolespermisos.objects.get(pk=pk)
    except Rolespermisos.DoesNotExist:
        return Response({'error': 'Rolpermiso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PUT':
        serializer = RolespermisosSerializer(rolpermiso, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
# Función para eliminar un Rolpermiso
@api_view(['DELETE'])
def rolespermisos_delete(request, pk):
    try:
        rolpermiso = Rolespermisos.objects.get(pk=pk)
    except Rolespermisos.DoesNotExist:
        return Response({'error': 'Rolpermiso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'DELETE':
        rolpermiso.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)