from django.urls import path
from .views      import get_all_ficha_cliente

urlpatterns = [
    path('api/fichaclientes/', get_all_ficha_cliente, name="get_all_ficha_cliente")
]