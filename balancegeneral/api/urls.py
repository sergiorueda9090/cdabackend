from django.urls import path
from .views import (obtener_balancegeneral, obtener_patrimonio_bruto, 
                    obtener_patrimonio_neto_endpoint, obtener_patrimonio_neto,
                    get_total_utilidad_nominal, total_utilidad_real, total_diferencia, gasto_totales_del_periodo)
#obtener_patrimonio_neto
urlpatterns = [
     path('api/balancegeneral/',                          obtener_balancegeneral,              name='balancegeneral'),
     path('api/balancegeneral/obtenertotaltarjetas',      obtener_patrimonio_bruto,            name='obtener_patrimonio_bruto'),
     path('api/balancegeneral/obtenercuatroxmilygastos',  obtener_patrimonio_neto_endpoint,    name='obtener_patrimonio_neto_endpoint'),
     path('api/balancegeneral/utilidadnominal',           get_total_utilidad_nominal,          name='get_total_utilidad_nominal'),
     
     path('api/balancegeneral/gastostotalesdelperiodo',   gasto_totales_del_periodo,          name='gasto_totales_del_periodo'),
     
     path('api/balancegeneral/utilidadreal',              total_utilidad_real,                 name='total_utilidad_real'),
     path('api/balancegeneral/totaldiferencia',           total_diferencia,                    name='total_diferencia'),
]
