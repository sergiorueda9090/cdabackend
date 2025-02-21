from django.urls import path
from .views import (
    listar_gastos,
    crear_gasto,
    obtener_gasto,
    actualizar_gasto,
    eliminar_gasto
)

urlpatterns = [
    path('api/gastos/',                   listar_gastos,    name='listar_gastos'),
    path('api/gastos/crear/',             crear_gasto,       name='crear_gasto'),
    path('api/gastos/<int:pk>/',          obtener_gasto,     name='obtener_gasto'),
    path('api/gastos/<int:pk>/update/',   actualizar_gasto,  name='actualizar_gasto'),
    path('api/gastos/<int:pk>/delete/',   eliminar_gasto,    name='eliminar_gasto'),
]
