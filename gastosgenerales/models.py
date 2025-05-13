from django.db                  import models
from django.utils.timezone      import now
from gastos.models              import Gastos
from registroTarjetas.models    import RegistroTarjetas
# Create your models here.
class Gastogenerales(models.Model):
    id_tipo_gasto       = models.ForeignKey(Gastos, on_delete=models.CASCADE)
    id_tarjeta_bancaria = models.ForeignKey(RegistroTarjetas, on_delete=models.CASCADE, verbose_name="Cuenta Bancaria Origen")
    fecha_ingreso       = models.DateTimeField(default=now, editable=False, verbose_name="Fecha de Ingreso")
    fecha_transaccion   = models.DateField(verbose_name="Fecha de Transacción")
    valor               = models.TextField(verbose_name="Valor")
    cuatro_por_mil      = models.TextField(null=True, blank=True)
    observacion         = models.TextField(blank=True, null=True, verbose_name="Observación")

    def __str__(self):
        return f"{self.valor}"

    class Meta:
        verbose_name = "Gasto general"
        verbose_name_plural = "Gastos generales"