from django.db import models

# Create your models here.
class Rolespermisos(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre