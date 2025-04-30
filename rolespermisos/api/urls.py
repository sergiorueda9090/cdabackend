from django.urls import path
from .views import rolespermisos_create, rolespermisos_detail, rolespermisos_list, rolespermisos_update, rolespermisos_delete

urlpatterns = [
    path('api/createpermision', rolespermisos_create, name="rolespermisos_create"),
    path('api/getpermision',    rolespermisos_detail, name="rolespermisos_detail"),
    path('api/lispermisions',   rolespermisos_update, name="rolespermisos_update"),
    path('api/deletepermision', rolespermisos_delete, name="rolespermisos_delete"),
]