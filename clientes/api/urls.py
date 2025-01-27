from django.urls import path
from . import views

urlpatterns = [
    path('api/',                   views.get_clientes,         name='get-clientes'),
    path('api/create/',            views.create_cliente,       name='create-cliente'),
    path('api/<int:pk>/',          views.get_cliente_detail,   name='get-cliente-detail'),
    path('api/<int:pk>/update/',   views.update_cliente,       name='update-cliente'),
    path('api/<int:pk>/delete/',   views.delete_cliente,       name='delete-cliente'),
    path('api/clientestramites/',  views.get_clientes_tramites, name='clientestramites'),
    path('api/verificar_cliente_y_generar_token/',  views.verificar_cliente_y_generar_token, name='verificar_cliente_y_generar_token'),
]
