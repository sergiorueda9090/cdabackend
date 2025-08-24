from django.urls import path
from .views import (
    listar_cargosnoregistrados,
    crear_cargosnoregistrados,
    obtener_cargosnoregistrados,
    actualizar_cargosnoregistrados,
    eliminar_cargosnoregistrados,
    listar_cargosnoregistrados_filtro
)

urlpatterns = [
    path('api/cargosnoregistrados/',                   listar_cargosnoregistrados,        name='listar_cargosnoregistrados'),
    path('api/cargosnoregistrados/crear/',             crear_cargosnoregistrados,           name='crear_cargosnoregistrados'),
    path('api/cargosnoregistrados/<int:pk>/',          obtener_cargosnoregistrados,         name='obtener_cargosnoregistrados'),
    path('api/cargosnoregistrados/<int:pk>/update/',   actualizar_cargosnoregistrados,      name='actualizar_cargosnoregistrados'),
    path('api/cargosnoregistrados/<int:pk>/delete/',   eliminar_cargosnoregistrados,        name='eliminar_cargosnoregistrados'),
    path('api/cargosnoregistrados/filtro/',            listar_cargosnoregistrados_filtro, name='listar_cargosnoregistrados_filtro')
]   
