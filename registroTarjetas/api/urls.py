from django.urls import path
from .views import crear_tarjeta,obtener_tarjetas, obtener_tarjeta, actualizar_tarjeta, eliminar_tarjeta

urlpatterns = [
    path('api/tarjeta/crear/',            crear_tarjeta,       name='crear_tarjeta'),
    path('api/tarjetas/',                 obtener_tarjetas,    name='obtener_tarjetas'),
    path('api/tarjeta/<int:id>',          obtener_tarjeta,     name='obtener_tarjeta'),
    path('api/tarjeta/<int:id>/update/',  actualizar_tarjeta,  name='actualizar_tarjeta'),
    path('api/tarjeta/<int:id>/delete/',  eliminar_tarjeta,    name='eliminar_tarjeta'),
]
