from django.urls import path
from etiquetas.api.views import (
    get_etiquetas, get_etiqueta, create_etiqueta, update_etiqueta, delete_etiqueta
)

urlpatterns = [
    path('api/etiquetas/',                  get_etiquetas,      name="get_etiquetas"),   # Obtener todas las etiquetas
    path('api/etiquetas/<int:id>/',         get_etiqueta,       name="get_etiqueta"),  # Obtener una etiqueta por ID
    path('api/etiquetas/create/',           create_etiqueta,    name="create_etiqueta"),  # Crear etiqueta
    path('api/etiquetas/update/<int:id>/',  update_etiqueta,    name="update_etiqueta"),  # Actualizar etiqueta
    path('api/etiquetas/delete/<int:id>/',  delete_etiqueta,    name="delete_etiqueta"),  # Eliminar etiqueta
]
