from rest_framework.decorators      import api_view, permission_classes, parser_classes
from rest_framework.parsers         import MultiPartParser, FormParser
from rest_framework.permissions     import IsAuthenticated
from rest_framework.response        import Response
from rest_framework                 import status
from django.shortcuts               import get_object_or_404
from users.models                   import User
from .serializers                   import UserSerializer
from users.decorators               import check_role  # Importa el decorador

# GET: Listar usuarios o detalle por ID
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1)
def get_users(request, user_id=None):
    user = request.user

    # Validar permiso basado en idrol
    if not user.idrol or user.idrol.id != 1:
        return Response(
            {"error": "No tienes permisos para acceder a este recurso."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        if user_id:
            user = get_object_or_404(User, id=user_id)
            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            users = User.objects.all()
            serializer = UserSerializer(users, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# POST: Crear usuario
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])  # Permitir archivos
@check_role(1)
def create_user(request):
    print(request.data)
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

# PUT: Actualizar usuario
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@check_role(1)
def update_user(request, user_id):
    print("user_id {}".format(user_id))
    user = get_object_or_404(User, id=user_id)
    print(user)
    serializer = UserSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

# DELETE: Eliminar usuario
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@check_role(1)
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    try:
        user.delete()
        return Response({'message': 'Usuario eliminado exitosamente'}, status=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_info(request):
    user        = request.user
    serializer  = UserSerializer(user)
    return Response(serializer.data)