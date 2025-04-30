from django.db import models
from django.contrib.auth.models import AbstractUser
from rolespermisos.models       import Rolespermisos

# Create your models here.
class User(AbstractUser):
    email  = models.EmailField(unique=True)
    image  = models.ImageField(upload_to='profile_pics/', null=True, blank=True)  # Imagen opcional
    idrol  = models.ForeignKey(Rolespermisos, on_delete=models.CASCADE, null=True, blank=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []