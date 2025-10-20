from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from etiquetas.models import Etiqueta
from etiquetas.api.serializer import EtiquetaSerializer
from rest_framework.permissions import IsAuthenticated

from users.decorators  import check_role

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1,2,3)
def get_etiquetas(request):
    etiquetas  = Etiqueta.objects.all()
    serializer = EtiquetaSerializer(etiquetas, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1)
def get_etiqueta(request, id):
    try:
        etiqueta = Etiqueta.objects.get(id=id)
        serializer = EtiquetaSerializer(etiqueta)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Etiqueta.DoesNotExist:
        return Response({"error": "Etiqueta no encontrada"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@check_role(1)
def create_etiqueta(request):
    serializer = EtiquetaSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@check_role(1)
def update_etiqueta(request, id):
    try:
        etiqueta = Etiqueta.objects.get(id=id)
    except Etiqueta.DoesNotExist:
        return Response({"error": "Etiqueta no encontrada"}, status=status.HTTP_404_NOT_FOUND)

    serializer = EtiquetaSerializer(etiqueta, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@check_role(1)
def delete_etiqueta(request, id):
    try:
        etiqueta = Etiqueta.objects.get(id=id)
        etiqueta.delete()
        return Response({"message": "Etiqueta eliminada correctamente"}, status=status.HTTP_204_NO_CONTENT)
    except Etiqueta.DoesNotExist:
        return Response({"error": "Etiqueta no encontrada"}, status=status.HTTP_404_NOT_FOUND)
