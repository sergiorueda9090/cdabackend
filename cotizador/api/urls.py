from django.urls import path
from .views import (
    create_cotizador,
    get_cotizadores,
    update_cotizador,
    delete_cotizador,
    get_cotizador,
    get_logs_cotizador,
    get_cotizadores_tramites,
    get_cotizadores_confirmacion_precios,
    get_cotizadores_pdfs,
    get_cotizadores_filter_date,
    search_cotizadores,
    update_cotizador_to_send_archivo,
    get_cotizadores_trasabilidad_filter_date,
    get_cotizadores_confirmacion_filter_date,
    get_cotizadores_pdf_filter_date,
    update_cotizador_devolver
)

urlpatterns = [
    path('api/',                                        get_cotizadores,                        name='get_cotizadores'),
    path('api/<int:pk>/',                               get_cotizador,                          name='get_cotizador'),
    path('api/create/',                                 create_cotizador,                       name='create_cotizador'),
    path('api/<int:pk>/update/',                        update_cotizador,                       name='update_cotizador'),
    path('api/<int:pk>/delete/',                        delete_cotizador,                       name='delete_cotizador'),
    path('get_logs_cotizador/api/<int:pk>/',            get_logs_cotizador,                     name='get_logs_cotizador'),
    path('get_logs_cotizador_tramites/api/',            get_cotizadores_tramites,               name='get_cotizadores_tramites'),
    path('get_cotizadores_confirmacion_precios/api/',   get_cotizadores_confirmacion_precios,   name='get_cotizadores_confirmacion_precios'),
    path('get_cotizadores_pdfs/api/',                   get_cotizadores_pdfs,                   name='get_cotizadores_pdfs'),
    path('get_cotizadores_filter_date/api/',            get_cotizadores_filter_date,            name='get_cotizadores_filter_date'),
    path('search_cotizadores/api/',                     search_cotizadores,                     name='search_cotizadores'),
    path('get_cotizadores_trasabilidad_filter_date/api/',get_cotizadores_trasabilidad_filter_date, name='get_cotizadores_trasabilidad_filter_date'),
    path('get_cotizadores_confirmacion_filter_date/api/',get_cotizadores_confirmacion_filter_date, name='get_cotizadores_confirmacion_filter_date'),
    path('get_cotizadores_pdf_filter_date/api/',         get_cotizadores_pdf_filter_date,          name='get_cotizadores_pdf_filter_date'),
    path('api/updatecotizadortosendarchivo/',            update_cotizador_to_send_archivo,         name='update_cotizador_to_send_archivo'),
    path('update_cotizador_devolver/api/<int:pk>/',      update_cotizador_devolver,                name='update_cotizador_devolver'),
]
