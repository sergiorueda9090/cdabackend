
from django.urls import path

from . import views

urlpatterns = [
    path('api/me/',          views.UserMeView.as_view(), name='user_me'),
]