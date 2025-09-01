# tarjetastrasladofondo/urls.py
from django.urls import path
from .views import crear_traslado

urlpatterns = [
    path('api/create/', crear_traslado, name='crear_traslado'),
]