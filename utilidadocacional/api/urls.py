from django.urls import path
from .views import (
    listar_utilidad_general,
    crear_utilidad_general,
    obtener_utilidad_general,
    actualizar_utilidad_general,
    eliminar_utilidad_general
)

urlpatterns = [
    path('api/utilidadocacional/',                    listar_utilidad_general,      name='listar_utilidad_general'),
    path('api/utilidadocacional/crear/',              crear_utilidad_general,       name='crear_utilidad_general'),
    path('api/utilidadocacional/<int:pk>/',           obtener_utilidad_general,     name='obtener_utilidad_general'),
    path('api/utilidadocacional/<int:pk>/update/',    actualizar_utilidad_general,  name='actualizar_utilidad_general'),
    path('api/utilidadocacional/<int:pk>/delete/',    eliminar_utilidad_general,    name='eliminar_utilidad_general'),
]
