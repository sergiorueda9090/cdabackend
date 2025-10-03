from django.urls import path
from .views import (
    listar_recepciones_pago,
    crear_recepcion_pago,
    obtener_recepcion_pago,
    actualizar_recepcion_pago,
    eliminar_recepcion_pago,
    listar_recepciones_pago_filtradas,
    obtener_recepcion_pago_cliente
)

urlpatterns = [
    path('api/recepciones/',                    listar_recepciones_pago,    name='listar_recepciones_pago'),
    path('api/recepciones/crear/',              crear_recepcion_pago,       name='crear_recepcion_pago'),
    path('api/recepciones/<int:pk>/',           obtener_recepcion_pago,     name='obtener_recepcion_pago'),
    path('api/recepciones/<int:pk>/update/',    actualizar_recepcion_pago,  name='actualizar_recepcion_pago'),
    path('api/recepciones/<int:pk>/delete/',    eliminar_recepcion_pago,    name='eliminar_recepcion_pago'),

    path('api/recepciones/listar_recepciones_pago_filtradas/',  listar_recepciones_pago_filtradas,      name='listar_recepciones_pago_filtradas'),
    path('api/recepcionescliente/<int:pk>/',                    obtener_recepcion_pago_cliente,     name='obtener_recepcion_pago_cliente'),
    
]
