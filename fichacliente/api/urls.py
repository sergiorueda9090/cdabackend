from django.urls import path
from .views      import get_all_ficha_cliente, get_all_ficha_cliente_agrupado

urlpatterns = [
    path('api/fichaclientes/', get_all_ficha_cliente, name="get_all_ficha_cliente"),
    path('api/fichaclientes/agrupado/', get_all_ficha_cliente_agrupado, name="get_all_ficha_cliente_agrupado"),
]