from django.db               import models
from registroTarjetas.models import RegistroTarjetas
from django.utils.timezone  import now

# Create your models here.
class Gastos(models.Model):
    name          = models.TextField(verbose_name="Nombre")
    observacion   = models.TextField(blank=True, null=True, verbose_name="Observación")
    fecha_ingreso = models.DateTimeField(default=now, editable=False, verbose_name="Fecha de Ingreso")

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = "Gastos"
        verbose_name_plural = "Gastos"