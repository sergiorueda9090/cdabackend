from django.urls import path
from .views import (obtener_balancegeneral, obtener_patrimonio_bruto, obtener_patrimonio_neto, get_total_utilidad_nominal, total_utilidad_real, total_diferencia)
#obtener_patrimonio_neto
urlpatterns = [
     path('api/balancegeneral/',                          obtener_balancegeneral,              name='balancegeneral'),
     path('api/balancegeneral/obtenertotaltarjetas',      obtener_patrimonio_bruto,            name='obtener_patrimonio_bruto'),
     path('api/balancegeneral/obtenercuatroxmilygastos',  obtener_patrimonio_neto,             name='obtener_patrimonio_neto'),
     path('api/balancegeneral/utilidadnominal',           get_total_utilidad_nominal,          name='get_total_utilidad_nominal'),
     path('api/balancegeneral/utilidadreal',              total_utilidad_real,                 name='total_utilidad_real'),
     path('api/balancegeneral/totaldiferencia',           total_diferencia,                    name='total_diferencia'),
]
