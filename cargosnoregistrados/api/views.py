from django.utils.dateparse import parse_date
from django.shortcuts import get_object_or_404
from rest_framework.decorators  import api_view
from rest_framework.response    import Response
from rest_framework             import status


from clientes.models            import Cliente
from registroTarjetas.models    import RegistroTarjetas
from cargosnoregistrados.models import Cargosnodesados
from .serializers               import CargosNoRegistradosSerializer
from users.decorators           import check_role

#Listar todas las cargo no registrado
@api_view(['GET'])
@check_role(1,2)
#@permission_classes([IsAuthenticated])
def listar_cargosnoregistrados(request):
    cargosnoregistradosAll = Cargosnodesados.objects.all()
    cargosnoregistradosAll_pago_data = []

    for cargonoregistrado in cargosnoregistradosAll:
        tarjeta = get_object_or_404(RegistroTarjetas, id=cargonoregistrado.id_tarjeta_bancaria_id)

        cliente = None
        if cargonoregistrado.id_cliente_id:  # 👉 solo si tiene cliente
            cliente = get_object_or_404(Cliente, id=cargonoregistrado.id_cliente_id)

        # Serializa cada cargo no registrado individualmente
        cargonoregistrado_serializer = CargosNoRegistradosSerializer(cargonoregistrado)
        cargonoregistrado_data = cargonoregistrado_serializer.data

        # Agregar datos personalizados
        cargonoregistrado_data['nombre_tarjeta'] = tarjeta.nombre_cuenta
        cargonoregistrado_data['valor'] = abs(int(cargonoregistrado.valor))

        if cliente:
            cargonoregistrado_data['nombre_cliente'] = cliente.nombre
            cargonoregistrado_data['color_cliente'] = cliente.color
        else:
            cargonoregistrado_data['nombre_cliente'] = None
            cargonoregistrado_data['color_cliente'] = None

        cuatro_por_mil = cargonoregistrado.cuatro_por_mil or 0
        cargonoregistrado_data['total'] = abs(int(cargonoregistrado.valor)) - abs(int(cuatro_por_mil))

        # Agregar el registro modificado a la lista
        cargosnoregistradosAll_pago_data.append(cargonoregistrado_data)

    return Response(cargosnoregistradosAll_pago_data, status=status.HTTP_200_OK)

#Crear una nuevo cargo no registrado
@api_view(['POST'])
@check_role(1,2)
#@permission_classes([IsAuthenticated])
def crear_cargosnoregistrados(request):
    required_fields = ["id_tarjeta_bancaria", "fecha_transaccion", "valor"]

    # Validar que los campos requeridos estén en la petición
    for field in required_fields:
        if field not in request.data or not request.data[field]:
            return Response({"error": f"El campo '{field}' es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)

    # Validar cliente solo si viene en el request
    cliente = None
    id_cliente = request.data.get("id_cliente")
    if id_cliente:
        try:
            cliente = Cliente.objects.get(pk=id_cliente)
        except Cliente.DoesNotExist:
            return Response({"error": "El cliente proporcionado no existe."}, status=status.HTTP_400_BAD_REQUEST)

    # Validar que la tarjeta bancaria exista
    try:
        tarjeta = RegistroTarjetas.objects.get(pk=request.data["id_tarjeta_bancaria"])
    except RegistroTarjetas.DoesNotExist:
        return Response({"error": "La cuenta bancaria proporcionada no existe."}, status=status.HTTP_400_BAD_REQUEST)

    # Validar que la fecha de transacción no sea futura
    from datetime import date
    fecha_transaccion = request.data.get("fecha_transaccion")
    if date.fromisoformat(fecha_transaccion) > date.today():
        return Response({"error": "La fecha de transacción no puede ser en el futuro."}, status=status.HTTP_400_BAD_REQUEST)

    # Crear la devolución
    valor = request.data["valor"]
    valor = int(valor.replace(".", ""))
    valor = abs(valor)

    if tarjeta.is_daviplata:
        cuatro_por_mil = 0
    else:
        cuatro_por_mil = 0 #int(abs(valor) * 0.004)

    devolucionCreate = Cargosnodesados.objects.create(
        id_cliente=cliente,  # 👉 si no hay cliente, va como None
        id_tarjeta_bancaria=tarjeta,
        fecha_transaccion=fecha_transaccion,
        valor=valor,
        cuatro_por_mil=cuatro_por_mil,
        observacion=request.data.get("observacion", "")
    )

    serializer = CargosNoRegistradosSerializer(devolucionCreate)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


#Obtener una devolución por ID
@api_view(['GET'])
@check_role(1,2)
#@permission_classes([IsAuthenticated])
def obtener_cargosnoregistrados(request, pk):
    try:
        cargosNoDeseadosGet = Cargosnodesados.objects.get(pk=pk)
    except Cargosnodesados.DoesNotExist:
        return Response({"error": "Cargos no deseados no encontrada."}, status=status.HTTP_404_NOT_FOUND)
    
    cargosNoDeseadosGet.valor = f"{abs(int(cargosNoDeseadosGet.valor)):,}".replace(",", ".")
    serializer = CargosNoRegistradosSerializer(cargosNoDeseadosGet)
    return Response(serializer.data, status=status.HTTP_200_OK)

#Actualizar una devolución
@api_view(['PUT'])
@check_role(1,2)
#@permission_classes([IsAuthenticated])
def actualizar_cargosnoregistrados(request, pk):
    try:
        cargoNoDeseadoGet = Cargosnodesados.objects.get(pk=pk)
    except Cargosnodesados.DoesNotExist:
        return Response({"error": "Cargo no deseado no encontrada."}, status=status.HTTP_404_NOT_FOUND)

    cliente_id = request.data.get("id_cliente")
    if cliente_id:
        try:
            cliente = Cliente.objects.get(pk=cliente_id)
            cargoNoDeseadoGet.id_cliente = cliente
        except Cliente.DoesNotExist:
            return Response({"error": "El cliente proporcionado no existe."}, status=status.HTTP_400_BAD_REQUEST)
    else:
        # Si llega vacío o null → limpiamos el cliente
        cargoNoDeseadoGet.id_cliente = None

    tarjeta_id = request.data.get("id_tarjeta_bancaria")
    if tarjeta_id:
        try:
            tarjeta = RegistroTarjetas.objects.get(pk=tarjeta_id)
            cargoNoDeseadoGet.id_tarjeta_bancaria = tarjeta
        except RegistroTarjetas.DoesNotExist:
            return Response({"error": "La cuenta bancaria proporcionada no existe."}, status=status.HTTP_400_BAD_REQUEST)
    
    # Validar que la fecha de transacción no sea futura
    from datetime import date
    fecha_transaccion = request.data.get("fecha_transaccion")
    if date.fromisoformat(fecha_transaccion) > date.today():
        return Response({"error": "La fecha de transacción no puede ser en el futuro."}, status=status.HTTP_400_BAD_REQUEST)

    cargoNoDeseadoGet.fecha_transaccion = request.data.get("fecha_transaccion", cargoNoDeseadoGet.fecha_transaccion)
 
    
    valor = request.data.get("valor", cargoNoDeseadoGet.valor)  # Obtener el valor del request o mantener el actual
    if isinstance(valor, str):  # Si el valor es una cadena, limpiarlo
        valor = int(valor.replace(".", ""))  # Eliminar separadores de miles y convertir a número
    cargoNoDeseadoGet.valor = abs(valor) #-abs(valor)  # Asegurar que siempre sea negativo
    
    cargoNoDeseadoGet.observacion = request.data.get("observacion", cargoNoDeseadoGet.observacion)

    if tarjeta.is_daviplata:
        cargoNoDeseadoGet.cuatro_por_mil = 0
    else:
        cargoNoDeseadoGet.cuatro_por_mil = 0 #int(abs(valor) * 0.004)
                                       
    cargoNoDeseadoGet.save()
    print(" cargoNoDeseadoGet ",cargoNoDeseadoGet)
    serializer = CargosNoRegistradosSerializer(cargoNoDeseadoGet)
    return Response(serializer.data, status=status.HTTP_200_OK)

#Eliminar una devolución
@api_view(['DELETE'])
@check_role(1,2)
#@permission_classes([IsAuthenticated])
def eliminar_cargosnoregistrados(request, pk):
    try:
        cargoNoDeseadoDelete = Cargosnodesados.objects.get(pk=pk)
        cargoNoDeseadoDelete.delete()
        return Response({"mensaje": "Cargo no deseado eliminada correctamente."}, status=status.HTTP_204_NO_CONTENT)
    except Cargosnodesados.DoesNotExist:
        return Response({"error": "Cargo no deseado no encontrada."}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@check_role(1,2)
#@permission_classes([IsAuthenticated])
def listar_cargosnoregistrados_filtro(request):
    from datetime import datetime, time
    fecha_inicio_str = request.GET.get('fechaInicio')
    fecha_fin_str    = request.GET.get('fechaFin')

    if not fecha_inicio_str or not fecha_fin_str:
        return Response({'error': 'Debe proporcionar fechaInicio y fechaFin como parámetros.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        fecha_inicio_date = parse_date(fecha_inicio_str)
        fecha_fin_date = parse_date(fecha_fin_str)

        # Convertir a datetime con horas ajustadas
        fecha_inicio = datetime.combine(fecha_inicio_date, time.min)  # 00:00:00
        fecha_fin = datetime.combine(fecha_fin_date, time.max)        # 23:59:59.999999

    except (ValueError, TypeError):
        return Response({'error': 'Formato de fecha inválido. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

    cargoNoDeseadoAll = Cargosnodesados.objects.filter(fecha_transaccion__range=[fecha_inicio, fecha_fin])
    cargonodeseado_pago_data = []

    for cargonodeseado in cargoNoDeseadoAll:
        tarjeta = get_object_or_404(RegistroTarjetas, id=cargonodeseado.id_tarjeta_bancaria_id)
        cliente = get_object_or_404(Cliente, id=cargonodeseado.id_cliente_id)

        cargonodeseado_serializer = CargosNoRegistradosSerializer(cargonodeseado)
        cargonodeseado_data = cargonodeseado_serializer.data

        cargonodeseado_data['nombre_tarjeta'] = tarjeta.nombre_cuenta
        cargonodeseado_data['nombre_cliente'] = cliente.nombre
        cargonodeseado_data['color_cliente'] = cliente.color
        cargonodeseado_data['valor'] = abs(int(cargonodeseado.valor))

        cuatro_por_mil = cargonodeseado.cuatro_por_mil
        if not cuatro_por_mil:
            cuatro_por_mil = 0

        cargonodeseado_data['total'] = cargonodeseado_data['valor'] - abs(int(cuatro_por_mil))

        cargonodeseado_pago_data.append(cargonodeseado_data)

    return Response(cargonodeseado_pago_data, status=status.HTTP_200_OK)



@api_view(['GET'])
@check_role(1,2)
#@permission_classes([IsAuthenticated])
def listar_cargosnoregistrados_cliente_filtro(request):
    from datetime import datetime, time
    fecha_inicio_str = request.GET.get('fechaInicio')
    fecha_fin_str    = request.GET.get('fechaFin')
    id_cliente       = request.GET.get('id_cliente')

    filtros = {}

    # Si vienen las fechas en los parámetros
    if fecha_inicio_str and fecha_fin_str:
        try:
            fecha_inicio_date = parse_date(fecha_inicio_str)
            fecha_fin_date = parse_date(fecha_fin_str)

            fecha_inicio = datetime.combine(fecha_inicio_date, time.min)  
            fecha_fin = datetime.combine(fecha_fin_date, time.max)        

            filtros['fecha_transaccion__range'] = [fecha_inicio, fecha_fin]

        except (ValueError, TypeError):
            return Response(
                {'error': 'Formato de fecha inválido. Use YYYY-MM-DD.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    # Si viene id_cliente
    if id_cliente:
        filtros['id_cliente_id'] = id_cliente

    # Consulta con filtros dinámicos
    cargos = Cargosnodesados.objects.filter(**filtros)
    resultado = []

    for cargo in cargos:
        cliente = get_object_or_404(Cliente, id=cargo.id_cliente_id)

        resultado.append({
            "fecha_transaccion": cargo.fecha_transaccion,
            "fecha_ingreso": cargo.fecha_ingreso,
            "valor": abs(int(cargo.valor)),
            "color_cliente": cliente.color
        })

    return Response(resultado, status=status.HTTP_200_OK)