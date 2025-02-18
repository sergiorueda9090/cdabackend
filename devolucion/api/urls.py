from django.urls import path
from .views import (
    listar_devoluciones,
    crear_devolucion,
    obtener_devolucion,
    actualizar_devolucion,
    eliminar_devolucion
)

urlpatterns = [
    path('api/devoluciones/',                   listar_devoluciones,    name='listar_devoluciones'),
    path('api/devoluciones/crear/',             crear_devolucion,       name='crear_devolucion'),
    path('api/devoluciones/<int:pk>/',          obtener_devolucion,     name='obtener_devolucion'),
    path('api/devoluciones/<int:pk>/update/',   actualizar_devolucion,  name='actualizar_devolucion'),
    path('api/devoluciones/<int:pk>/delete/',   eliminar_devolucion,    name='eliminar_devolucion'),
]
