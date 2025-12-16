from django.shortcuts import get_object_or_404
from rest_framework.decorators  import api_view, permission_classes
from rest_framework.response    import Response
from rest_framework             import status

from gastosgenerales.models     import Gastogenerales
from gastos.models              import Gastos
from registroTarjetas.models    import RegistroTarjetas
from .serializers               import GastogeneralesSerializer

from rest_framework.permissions import IsAuthenticated

from datetime import datetime
from django.db.models   import Q
from users.decorators   import check_role
from django.http import HttpResponse
from tempfile import NamedTemporaryFile
import pandas as pd
#Listar todas las recepciones de pago
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1,2)
def listar_gastos_generales(request):
    try:
        gastos = Gastogenerales.objects.all().order_by('-fecha_ingreso')
        total_gastos_data = []

        for gasto in gastos:
            try:
                # Ensure we are getting the correct ID
                tarjeta_id = gasto.id_tarjeta_bancaria.pk  # Get the numeric ID
                gasto_id   = gasto.id_tipo_gasto.pk
                
                gasto.valor = abs(int(gasto.valor))
                # Fetch related objects
                tarjeta     = get_object_or_404(RegistroTarjetas, id=tarjeta_id)
                gasto_model = get_object_or_404(Gastos, id=gasto_id)

                # Serialize gasto
                gastos_serializer = GastogeneralesSerializer(gasto)
                gastos_data = gastos_serializer.data
                
                # Add extra data
                gastos_data['nombre_tarjeta'] = tarjeta.nombre_cuenta
                gastos_data['nombre_gasto'] = gasto_model.name

                # Append to result
                total_gastos_data.append(gastos_data)
                print("total_gastos_data ",total_gastos_data)
            except Exception as e:
                print(f"Error procesando recepción ID {gasto.id}: {e}")
                return Response(
                    {"error": f"Error procesando recepción ID {gasto.id}: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(total_gastos_data, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"Error en la función listar_gastos_generales: {e}")
        return Response(
            {"error": f"Error en la función listar_gastos_generales: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Crear una nueva recepción de pago
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@check_role(1,2)
def crear_gasto_generale(request):
    required_fields = ["id_tipo_gasto", "id_tarjeta_bancaria", "fecha_transaccion", "valor"]

    # Validar que los campos requeridos estén en la petición
    for field in required_fields:
        if field not in request.data or not request.data[field]:
            return Response({"error": f"El campo '{field}' es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)

    # Validar que el cliente exista
    try:
        gasto = Gastos.objects.get(pk=request.data["id_tipo_gasto"])
    except Gastos.DoesNotExist:
        return Response({"error": "El Gasto proporcionado no existe."}, status=status.HTTP_400_BAD_REQUEST)

    # Validar que la tarjeta bancaria exista
    try:
        tarjeta = RegistroTarjetas.objects.get(pk=request.data["id_tarjeta_bancaria"])
    except RegistroTarjetas.DoesNotExist:
        return Response({"error": "La tarjeta bancaria proporcionada no existe."}, status=status.HTTP_400_BAD_REQUEST)

    # Validar que la fecha de transacción no sea futura
    from datetime import date
    fecha_transaccion = request.data.get("fecha_transaccion")
    if date.fromisoformat(fecha_transaccion) > date.today():
        return Response({"error": "La fecha de transacción no puede ser en el futuro."}, status=status.HTTP_400_BAD_REQUEST)

    # Crear la recepción de pago
    valor = request.data["valor"]
    valor = int(valor.replace(".", ""))
    valor = -abs(valor)

    if tarjeta.is_daviplata:
        cuatro_por_mil = 0
    else:
        cuatro_por_mil = int(abs(valor) * 0.004)
    
    recepcion_gasto_general = Gastogenerales.objects.create(
        id_tipo_gasto       = gasto,
        id_tarjeta_bancaria = tarjeta,
        fecha_transaccion   = request.data["fecha_transaccion"],
        valor               = valor,
        cuatro_por_mil      = cuatro_por_mil,
        observacion         = request.data.get("observacion", "")
    )

    serializer = GastogeneralesSerializer(recepcion_gasto_general)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

#Obtener una recepción de pago por ID
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1,2)
def obtener_gasto_generale(request, pk):
    try:
        recepcion = Gastogenerales.objects.get(pk=pk)
    except Gastogenerales.DoesNotExist:
        return Response({"error": "Recepción de gastos generales no encontrada."}, status=status.HTTP_404_NOT_FOUND)
    recepcion.valor = f"{abs(int(recepcion.valor)):,}".replace(",", ".")
    serializer = GastogeneralesSerializer(recepcion)
    return Response(serializer.data, status=status.HTTP_200_OK)

#Actualizar una recepción de pago
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@check_role(1,2)
def actualizar_gasto_generale(request, pk):
    try:
        recepcion = Gastogenerales.objects.get(pk=pk)
    except Gastogenerales.DoesNotExist:
        return Response({"error": "Recepción de gastos generales no encontrada."}, status=status.HTTP_404_NOT_FOUND)

    # Validar cliente si se envía en la solicitud
    id_tipo_gasto = request.data.get("id_tipo_gasto")
    if id_tipo_gasto:
        try:
            gasto = Gastos.objects.get(pk=id_tipo_gasto)
            recepcion.id_tipo_gasto = gasto
        except Gastos.DoesNotExist:
            return Response({"error": "El gasto proporcionado no existe."}, status=status.HTTP_400_BAD_REQUEST)

    # Validar tarjeta bancaria si se envía en la solicitud
    tarjeta_id = request.data.get("id_tarjeta_bancaria")
    if tarjeta_id:
        try:
            tarjeta = RegistroTarjetas.objects.get(pk=tarjeta_id)
            recepcion.id_tarjeta_bancaria = tarjeta
        except RegistroTarjetas.DoesNotExist:
            return Response({"error": "La tarjeta bancaria proporcionada no existe."}, status=status.HTTP_400_BAD_REQUEST)

    # Actualizar otros campos
    #recepcion.cuenta_bancaria_destino = request.data.get("cuenta_bancaria_destino", recepcion.cuenta_bancaria_destino)
    recepcion.fecha_transaccion = request.data.get("fecha_transaccion", recepcion.fecha_transaccion)
    valor = request.data.get("valor", recepcion.valor)  # Obtener el valor del request o mantener el actual
    if isinstance(valor, str):  # Si el valor es una cadena, limpiarlo
        valor = int(valor.replace(".", ""))  # Eliminar separadores de miles y convertir a número
    
    recepcion.valor         =  -abs(valor)  # Asegurar que siempre sea negativo
    recepcion.observacion   = request.data.get("observacion", recepcion.observacion)

    if tarjeta.is_daviplata:
        recepcion.cuatro_por_mil = 0
    else:
        recepcion.cuatro_por_mil = int(abs(valor) * 0.004)

    recepcion.save()

    serializer = GastogeneralesSerializer(recepcion)
    return Response(serializer.data, status=status.HTTP_200_OK)

#Eliminar una recepción de pago
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@check_role(1,2)
def eliminar_gasto_generale(request, pk):
    try:
        recepcion = Gastogenerales.objects.get(pk=pk)
        recepcion.delete()
        return Response({"mensaje": "Recepción de Gasto generale eliminada correctamente."}, status=status.HTTP_204_NO_CONTENT)
    except Gastogenerales.DoesNotExist:
        return Response({"error": "Recepción de Gasto generale no encontrada."}, status=status.HTTP_404_NOT_FOUND)
    

def parse_date_with_defaults(date_str, is_end=False):
    if not date_str:
        return None
    
    parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
    if is_end:
        parsed_date = parsed_date.replace(hour=23, minute=59, second=59)
    else:
        parsed_date = parsed_date.replace(hour=0, minute=0, second=0)
    return parsed_date

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1,2)
def listar_gastos_generales_filtradas(request):
    fecha_inicio = parse_date_with_defaults(request.GET.get('fechaInicio'))
    fecha_fin    = parse_date_with_defaults(request.GET.get('fechaFin'), is_end=True)

    filtro_fecha = Q()
    if fecha_inicio and fecha_fin:
        filtro_fecha = Q(fecha_transaccion__range=(fecha_inicio, fecha_fin))
    elif fecha_inicio:
        filtro_fecha = Q(fecha_transaccion__gte=fecha_inicio)
    elif fecha_fin:
        filtro_fecha = Q(fecha_transaccion__lte=fecha_fin)
    try:
        gastos = Gastogenerales.objects.filter(filtro_fecha)
        total_gastos_data = []

        for gasto in gastos:
            try:
                # Ensure we are getting the correct ID
                tarjeta_id = gasto.id_tarjeta_bancaria.pk  # Get the numeric ID
                gasto_id   = gasto.id_tipo_gasto.pk

                # Fetch related objects
                tarjeta     = get_object_or_404(RegistroTarjetas, id=tarjeta_id)
                gasto_model = get_object_or_404(Gastos, id=gasto_id)

                # Serialize gasto
                gastos_serializer = GastogeneralesSerializer(gasto)
                gastos_data = gastos_serializer.data

                # Add extra data
                gastos_data['nombre_tarjeta'] = tarjeta.nombre_cuenta
                gastos_data['nombre_gasto'] = gasto_model.name

                # Append to result
                total_gastos_data.append(gastos_data)
                print("total_gastos_data ",total_gastos_data)
            except Exception as e:
                print(f"Error procesando recepción ID {gasto.id}: {e}")
                return Response(
                    {"error": f"Error procesando recepción ID {gasto.id}: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(total_gastos_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {"error": f"Error en la función total_utilidades_data: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@check_role(1,2)
def download_excel(request):
    """
    Endpoint para descargar un archivo Excel con los gastos generales filtrados por fecha.
    Parámetros opcionales: fechaInicio, fechaFin
    """
    try:
        # Obtener los parámetros de fecha de la URL
        fecha_inicio = parse_date_with_defaults(request.GET.get('fechaInicio'))
        fecha_fin = parse_date_with_defaults(request.GET.get('fechaFin'), is_end=True)

        # Construir el filtro de fecha
        filtro_fecha = Q()
        if fecha_inicio and fecha_fin:
            filtro_fecha = Q(fecha_transaccion__range=(fecha_inicio, fecha_fin))
        elif fecha_inicio:
            filtro_fecha = Q(fecha_transaccion__gte=fecha_inicio)
        elif fecha_fin:
            filtro_fecha = Q(fecha_transaccion__lte=fecha_fin)

        # Obtener los gastos generales filtrados
        gastos = Gastogenerales.objects.filter(filtro_fecha).order_by('-fecha_transaccion')

        # Preparar los datos para el DataFrame
        datos_excel = []
        total_valor = 0
        total_cuatro_por_mil = 0

        for gasto in gastos:
            try:
                # Obtener información de la tarjeta y tipo de gasto
                tarjeta = gasto.id_tarjeta_bancaria
                tipo_gasto = gasto.id_tipo_gasto

                # Preparar fila de datos
                fila = {
                    'ID': gasto.id,
                    'Fecha Ingreso': gasto.fecha_ingreso,
                    'Fecha Transacción': gasto.fecha_transaccion,
                    'Descripción': gasto.observacion if gasto.observacion else '',
                    'Valor': abs(int(gasto.valor)),
                    'Cuatro por Mil': int(gasto.cuatro_por_mil) if gasto.cuatro_por_mil else 0,
                    'Tipo de Gasto': tipo_gasto.name if tipo_gasto else '',
                    'Tarjeta/Cuenta': tarjeta.nombre_cuenta if tarjeta else '',
                    'Banco': tarjeta.banco if tarjeta else ''
                }

                datos_excel.append(fila)
                total_valor += abs(int(gasto.valor))
                total_cuatro_por_mil += int(gasto.cuatro_por_mil) if gasto.cuatro_por_mil else 0

            except Exception as e:
                print(f"Error procesando gasto ID {gasto.id}: {e}")
                continue

        # Crear DataFrame
        if datos_excel:
            df = pd.DataFrame(datos_excel)

            # Formatear fechas
            if 'Fecha Ingreso' in df.columns:
                df['Fecha Ingreso'] = pd.to_datetime(df['Fecha Ingreso']).dt.tz_localize(None)
            if 'Fecha Transacción' in df.columns:
                df['Fecha Transacción'] = pd.to_datetime(df['Fecha Transacción']).dt.strftime('%Y-%m-%d')
        else:
            # DataFrame vacío con las columnas correctas
            df = pd.DataFrame(columns=['ID', 'Fecha Ingreso', 'Fecha Transacción', 'Descripción',
                                      'Valor', 'Cuatro por Mil', 'Tipo de Gasto', 'Tarjeta/Cuenta', 'Banco'])

        # Crear DataFrame con totales
        df_totales = pd.DataFrame({
            'Concepto': ['Total Gastos Generales', 'Total Cuatro por Mil', 'TOTAL'],
            'Valor': [total_valor, total_cuatro_por_mil, total_valor + total_cuatro_por_mil]
        })

        # Crear DataFrame con información del reporte
        rango_fechas = f"Desde {fecha_inicio.strftime('%Y-%m-%d') if fecha_inicio else 'Inicio'} hasta {fecha_fin.strftime('%Y-%m-%d') if fecha_fin else 'Fin'}"
        df_info = pd.DataFrame({
            'Campo': ['Reporte', 'Rango de Fechas', 'Fecha de Generación', 'Cantidad de Registros'],
            'Valor': ['Gastos Generales', rango_fechas, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), len(datos_excel)]
        })

        # Crear archivo Excel temporal
        with NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            with pd.ExcelWriter(tmp.name, engine="xlsxwriter") as writer:
                # Escribir las hojas
                df_info.to_excel(writer, sheet_name="Información", index=False)
                df.to_excel(writer, sheet_name="Gastos Generales", index=False)
                df_totales.to_excel(writer, sheet_name="Totales", index=False)

                # Obtener el workbook y worksheet para formatear
                workbook = writer.book
                worksheet_gastos = writer.sheets['Gastos Generales']

                # Formato para números
                money_format = workbook.add_format({'num_format': '#,##0'})

                # Aplicar formato a columnas de valores (asumiendo que Valor está en columna E y Cuatro por Mil en F)
                if not df.empty:
                    worksheet_gastos.set_column('E:F', 15, money_format)

            # Leer el archivo y enviarlo como respuesta
            with open(tmp.name, "rb") as excel_file:
                response = HttpResponse(
                    excel_file.read(),
                    content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                # Nombre del archivo
                fecha_str = f"{fecha_inicio.strftime('%Y%m%d')}_{fecha_fin.strftime('%Y%m%d')}" if fecha_inicio and fecha_fin else datetime.now().strftime('%Y%m%d')
                filename = f"Gastos_Generales_{fecha_str}.xlsx"
                response["Content-Disposition"] = f'attachment; filename="{filename}"'

        return response

    except Exception as e:
        print(f"Error al generar el archivo Excel: {e}")
        return Response(
            {"error": f"Error al generar el archivo Excel: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )