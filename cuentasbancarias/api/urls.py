from django.urls import path
from .views import (obtener_cuentas,       obtener_cuenta,      crear_cuenta, 
                    actualizar_cuenta,     eliminar_cuenta,     obtener_datos_cuenta, 
                    download_report_excel, cuentasbancarias_filter_date)

urlpatterns = [
    path('api/cuentas/crear/',            crear_cuenta,       name='crear_cuenta'),
    path('api/cuentas/',                  obtener_cuentas,    name='obtener_cuentas'),
    path('api/cuenta/<int:id>',           obtener_cuenta,     name='obtener_cuenta'),
    path('api/cuentas/<int:id>/update/',  actualizar_cuenta,  name='actualizar_cuenta'),
    path('api/cuentas/<int:id>/delete/',  eliminar_cuenta,    name='eliminar_cuenta'),
    path('api/cuenta/<int:id>/obtener_datos_cuenta/',               obtener_datos_cuenta,               name='obtener_datos_cuenta'),
    path('api/cuenta/<int:id>/get_cuentasbancarias_filter_date/',   cuentasbancarias_filter_date,       name='cuentasbancarias_filter_date'),
    path('api/cuenta/<int:id>/download_report_excel/',              download_report_excel,              name='download_report_excel'),
]
