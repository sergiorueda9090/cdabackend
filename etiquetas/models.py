from django.db import models

class Etiqueta(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    color  = models.CharField(max_length=100, null=True, blank=True)
    
    def __str__(self):
        return self.nombre
