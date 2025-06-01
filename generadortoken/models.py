from django.db import models
from datetime import datetime, timedelta

class GeneradorToken(models.Model):
    identificacion = models.CharField(max_length=20, verbose_name="Número de Identificación")
    token = models.CharField(max_length=6, verbose_name="Token Generado")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")

    def ha_expirado(self):
        # Opcional: 10 minutos de validez
        return datetime.now() > self.fecha_creacion + timedelta(minutes=10)
    
    def __str__(self):
        return f"{self.identificacion} - {self.token}"
