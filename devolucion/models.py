from django.db              import models
from django.utils.timezone  import now
from clientes.models         import Cliente
from registroTarjetas.models import RegistroTarjetas

class Devolucion(models.Model):
    cliente             = models.ForeignKey(Cliente, on_delete=models.CASCADE, verbose_name="Cliente")
    id_tarjeta_bancaria = models.ForeignKey(RegistroTarjetas, on_delete=models.CASCADE, verbose_name="Cuenta Bancaria Origen")
    fecha_ingreso       = models.DateTimeField(default=now, editable=False, verbose_name="Fecha de Ingreso")
    fecha_transaccion   = models.DateField(verbose_name="Fecha de Transacción")
    valor               = models.TextField(verbose_name="Valor")
    observacion         = models.TextField(blank=True, null=True, verbose_name="Observación")

    def __str__(self):
        return f"{self.cliente.nombre} - {self.valor}"

    class Meta:
        verbose_name = "Devolución"
        verbose_name_plural = "Devoluciones"
