from django.urls import path
from .views import (obtener_balancegeneral)

urlpatterns = [
     path('api/balancegeneral/',  obtener_balancegeneral, name='balancegeneral'),
]
