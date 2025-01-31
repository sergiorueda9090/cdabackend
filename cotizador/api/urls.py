from django.urls import path
from .views import (
    create_cotizador,
    get_cotizadores,
    update_cotizador,
    delete_cotizador,
    get_cotizador,
    get_logs_cotizador,
    get_cotizadores_tramites,
    get_cotizadores_confirmacion_precios
)

urlpatterns = [
    path('api/',                                        get_cotizadores,                        name='get_cotizadores'),
    path('api/<int:pk>/',                               get_cotizador,                          name='get_cotizador'),
    path('api/create/',                                 create_cotizador,                       name='create_cotizador'),
    path('api/<int:pk>/update/',                        update_cotizador,                       name='update_cotizador'),
    path('api/<int:pk>/delete/',                        delete_cotizador,                       name='delete_cotizador'),
    path('get_logs_cotizador/api/<int:pk>/',            get_logs_cotizador,                     name='get_logs_cotizador'),
    path('get_logs_cotizador_tramites/api/',            get_cotizadores_tramites,               name='get_cotizadores_tramites'),
    path('get_cotizadores_confirmacion_precios/api/',   get_cotizadores_confirmacion_precios,   name='get_cotizadores_confirmacion_precios')
]
