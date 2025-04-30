from django.urls import path
from .views      import get_all_fecha_proveedores, get_ficha_proveedores, get_ficha_proveedor_por_id

urlpatterns = [
    path('api/fichaproveedores/',           get_all_fecha_proveedores,  name="get_all_fecha_proveedores"),
    path('api/get_ficha_proveedores/',      get_ficha_proveedores,      name="get_ficha_proveedores"),
    path('api/get_ficha_proveedor_por_id/', get_ficha_proveedor_por_id, name="get_ficha_proveedor_por_id"),
]