from django.urls import path
from .views      import get_ficha_utilidades


urlpatterns = [
    path('api/utilidades/', get_ficha_utilidades,  name="utilidades"),
]