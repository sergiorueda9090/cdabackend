from django.urls import path
from .views      import get_all_cotizadores, sent_to_tramites, get_cotizador


urlpatterns = [
    path('api/historialtramitesemitidos/',                          get_all_cotizadores,  name="historialtramitesemitidos"),
    path('api/senttohistorialtramitesemitidos/<int:idcotizador>/',  sent_to_tramites,     name="senttohistorialtramitesemitidos"),
    path('api/gethistorialtramitesemitidos/<int:idcotizador>/',     get_cotizador,        name="gethistorialtramitesemitidos")
]