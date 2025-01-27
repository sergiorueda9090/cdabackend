from django.db import models

class GeneradorToken(models.Model):
    identificacion = models.CharField(max_length=20, verbose_name="Número de Identificación")
    token = models.CharField(max_length=6, verbose_name="Token Generado")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")

    def __str__(self):
        return f"{self.identificacion} - {self.token}"
