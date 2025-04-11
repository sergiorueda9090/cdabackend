from django.urls import path
from .views import (get_proveedores, get_proveedor, create_proveedor, update_proveedor, delete_proveedor)

urlpatterns = [
    path('api/',                                get_proveedores, name='get_proveedores'),
    path('api/proveedores/<int:pk>/',           get_proveedor, name='get_proveedor'),
    path('api/proveedores/create/',             create_proveedor, name='create_proveedor'),
    path('api/proveedores/update/<int:pk>/',    update_proveedor, name='update_proveedor'),
    path('api/proveedores/delete/<int:pk>/',    delete_proveedor, name='delete_proveedor'),
]
