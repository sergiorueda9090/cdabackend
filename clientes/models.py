from django.db import models

class Cliente(models.Model):
    nombre      = models.CharField(max_length=100, unique=True)
    apellidos   = models.CharField(max_length=100)
    telefono    = models.CharField(max_length=20, blank=True, null=True)
    direccion   = models.TextField(blank=True, null=True)
    color       = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} {self.apellidos}"


class PrecioLey(models.Model):
    cliente     = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='precios_ley')
    descripcion = models.CharField(max_length=255)
    precio_ley  = models.CharField(max_length=255)
    comision    = models.CharField(max_length=255)
    fecha       = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.descripcion} - {self.precio_ley}"