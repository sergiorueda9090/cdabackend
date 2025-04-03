from django.urls import path
from .views      import get_all_cotizadores, sent_to_tramites, get_cotizador


urlpatterns = [
    path('api/archivocotizacionesantiguas/',      get_all_cotizadores,  name="archivocotizacionesantiguas"),
    path('api/senttotramites/<int:idcotizador>/', sent_to_tramites,    name="sent_to_tramites"),
    path('api/getcotizador/<int:idcotizador>/',   get_cotizador,       name="get_cotizador")
]