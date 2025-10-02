from django.db              import models
from django.utils.timezone  import now
from registroTarjetas.models import RegistroTarjetas

class Tarjetastrasladofondo(models.Model):
    id_tarjeta_bancaria_envia = models.ForeignKey(
        RegistroTarjetas,
        on_delete=models.CASCADE,
        related_name="traslados_enviados",
        verbose_name="Cuenta Bancaria Envia"
    )
    id_tarjeta_bancaria_recibe = models.ForeignKey(
        RegistroTarjetas,
        on_delete=models.CASCADE,
        related_name="traslados_recibidos",
        verbose_name="Cuenta Bancaria Recibe"
    )
    fecha_ingreso     = models.DateTimeField(default=now, editable=False, verbose_name="Fecha de Ingreso")
    fecha_transaccion = models.DateTimeField(default=now, editable=False, verbose_name="Fecha de Transacción")
    valor             = models.TextField(verbose_name="Valor")
    cuatro_por_mil    = models.TextField(null=True, blank=True)
    observacion       = models.TextField(blank=True, null=True, verbose_name="Observación")

    def __str__(self):
        return f"Traslado {self.valor} el {self.fecha_transaccion} de {self.id_tarjeta_bancaria_envia} → {self.id_tarjeta_bancaria_recibe}"

    class Meta:
        verbose_name = "Tarjetastrasladofondo"
        verbose_name_plural = "tarjetastrasladofondos"
        db_table = "tarjetastrasladofondo"