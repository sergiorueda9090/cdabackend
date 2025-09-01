# tarjetastrasladofondo/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from tarjetastrasladofondo.models import Tarjetastrasladofondo
from .serializers import TarjetastrasladofondoSerializer

@api_view(['POST'])
def crear_traslado(request):
    serializer = TarjetastrasladofondoSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
