from django.db          import models
from etiquetas.models   import Etiqueta
# Create your models here.
class Proveedor(models.Model):
    nombre          = models.CharField(max_length=255)
    etiqueta        = models.ForeignKey(Etiqueta, on_delete=models.CASCADE)
    fecha_creacion  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre