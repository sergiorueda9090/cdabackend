from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class User(AbstractUser):
    email = models.EmailField(unique=True)
    image = models.ImageField(upload_to='profile_pics/', null=True, blank=True)  # Imagen opcional
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []