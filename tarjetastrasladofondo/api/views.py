# tarjetastrasladofondo/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from tarjetastrasladofondo.models import Tarjetastrasladofondo
from registroTarjetas.models      import RegistroTarjetas
from .serializers import TarjetastrasladofondoSerializer

@api_view(['POST'])
def crear_traslado(request):
    id_tarjeta_envia  = request.data.get('id_tarjeta_bancaria_envia')
    id_tarjeta_recibe = request.data.get('id_tarjeta_bancaria_recibe')
    # ✅ Validar si falta alguna tarjeta
    if not id_tarjeta_envia:
        return Response(
            {"error": "Debe seleccionar la tarjeta de origen."},
            status=status.HTTP_400_BAD_REQUEST
        )
    if not id_tarjeta_recibe:
        return Response(
            {"error": "Debe seleccionar la tarjeta de destino."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validar que 'id_tarjeta_bancaria_envia' y 'id_tarjeta_bancaria_recibe' no sean iguales
    if request.data.get('id_tarjeta_bancaria_envia') == request.data.get('id_tarjeta_bancaria_recibe'):
        return Response(
            {"error": "La tarjeta de origen y destino no pueden ser la misma."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        tarjeta = RegistroTarjetas.objects.get(
            id=request.data['id_tarjeta_bancaria_envia']
        )
    except RegistroTarjetas.DoesNotExist:
        return Response({"error": "La tarjeta no existe"}, status=status.HTTP_400_BAD_REQUEST)

    # Copiar los datos para que sean mutables
    data = request.data.copy()

    # calcular el 4 x 1000 (0.4%) si aplica
    valor = float(data['valor'])
    if tarjeta.is_daviplata == 0:  # si aplica el cuatro por mil
        data['cuatro_por_mil'] = round(valor * 0.004, 2)
    else:
        data['cuatro_por_mil'] = 0

    print(data['cuatro_por_mil'])

    serializer = TarjetastrasladofondoSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)