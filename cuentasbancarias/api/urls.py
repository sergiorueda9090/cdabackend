from django.urls import path
from .views import obtener_cuentas,obtener_cuenta, crear_cuenta, actualizar_cuenta, eliminar_cuenta

urlpatterns = [
    path('api/cuentas/crear/',            crear_cuenta,       name='crear_cuenta'),
    path('api/cuentas/',                  obtener_cuentas,    name='obtener_cuentas'),
    path('api/cuenta/<int:id>',           obtener_cuenta,    name='obtener_cuenta'),
    path('api/cuentas/<int:id>/update/',  actualizar_cuenta,  name='actualizar_cuenta'),
    path('api/cuentas/<int:id>/delete/',  eliminar_cuenta,    name='eliminar_cuenta'),
]
