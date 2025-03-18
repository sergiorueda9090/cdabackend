from django.urls import path
from .views import (
    listar_gastos_generales,
    crear_gasto_generale,
    obtener_gasto_generale,
    actualizar_gasto_generale,
    eliminar_gasto_generale,
    listar_gastos_generales_filtradas
)

urlpatterns = [
    path('api/gastosgenerales/',                    listar_gastos_generales,    name='listar_gastos_generales'),
    path('api/gastosgenerales/crear/',              crear_gasto_generale,       name='crear_gasto_generale'),
    path('api/gastosgenerales/<int:pk>/',           obtener_gasto_generale,     name='obtener_gasto_generale'),
    path('api/gastosgenerales/<int:pk>/update/',    actualizar_gasto_generale,  name='actualizar_gasto_generale'),
    path('api/gastosgenerales/<int:pk>/delete/',    eliminar_gasto_generale,    name='eliminar_gasto_generale'),

   path('api/gastosgenerales/listar_gastos_generales_filtradas/',    listar_gastos_generales_filtradas,    name='listar_gastos_generales_filtradas'),
]
