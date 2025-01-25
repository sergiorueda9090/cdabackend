from django.urls import path
from .views import create_tramite, get_tramites, update_tramite, delete_tramite, get_tramite, get_logs_tramite

urlpatterns = [
    path('api/',                        get_tramites,       name='get_tramites'),
    path('api/<int:pk>/',               get_tramite,        name='get_tramite'),
    path('api/create/',                 create_tramite,     name='create_tramite'),
    path('api/<int:pk>/update/',        update_tramite,     name='update_tramite'),
    path('api/<int:pk>/delete/',        delete_tramite,     name='delete_tramite'),
    path('get_logs_tramite/api/<int:pk>/',  get_logs_tramite,   name='get_logs_tramite'),
]