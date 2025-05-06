from django.urls import path
from .views import (
    listar_ajustessaldos,
    crear_ajustessaldo,
    obtener_ajustessaldo,
    actualizar_ajustessaldo,
    eliminar_ajustessaldo,
    listar_ajustessaldo_filtradas
)

urlpatterns = [
    path('api/ajustessaldo/',                   listar_ajustessaldos,     name='listar_ajustessaldos'),
    path('api/ajustessaldo/crear/',             crear_ajustessaldo,       name='crear_ajustessaldo'),
    path('api/ajustessaldo/<int:pk>/',          obtener_ajustessaldo,     name='obtener_ajustessaldo'),
    path('api/ajustessaldo/<int:pk>/update/',   actualizar_ajustessaldo,  name='actualizar_ajustessaldo'),
    path('api/ajustessaldo/<int:pk>/delete/',   eliminar_ajustessaldo,    name='eliminar_ajustessaldo'),
    path('api/ajustessaldo/listar_ajustessaldo_filtradas/',   listar_ajustessaldo_filtradas,    name='listar_ajustessaldo_filtradas'),
]
