from django.urls import path
from .views import get_users, create_user, update_user, delete_user, get_user_info

urlpatterns = [
    # Listar todos los usuarios
    path('api/users/', get_users, name='get_users'),
    
    # Detalle de un usuario por ID
    path('api/users/<int:user_id>/', get_users, name='get_user'),
    
    # Crear un usuario
    path('api/users/create/', create_user, name='create_user'),
    
    # Actualizar un usuario por ID
    path('api/users/<int:user_id>/update/', update_user, name='update_user'),
    
    # Eliminar un usuario por ID
    path('api/users/<int:user_id>/delete/', delete_user, name='delete_user'),

    # Obtener los datos logeados
    path('api/user/', get_user_info, name='get_user_info'),
]
