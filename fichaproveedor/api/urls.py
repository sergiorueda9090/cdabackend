from django.urls import path
from .views      import get_all_fecha_proveedores

urlpatterns = [
    path('api/fichaproveedores/', get_all_fecha_proveedores, name="get_all_fecha_proveedores")
]