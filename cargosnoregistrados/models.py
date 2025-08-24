from django.db              import models
from django.utils.timezone  import now
from clientes.models         import Cliente
from registroTarjetas.models import RegistroTarjetas

class Cargosnodesados(models.Model):
    id_cliente          = models.ForeignKey(Cliente, on_delete=models.CASCADE, verbose_name="Cliente",null=True, blank=True)
    id_tarjeta_bancaria = models.ForeignKey(RegistroTarjetas, on_delete=models.CASCADE, verbose_name="Cuenta Bancaria Origen")
    fecha_ingreso       = models.DateTimeField(default=now, editable=False, verbose_name="Fecha de Ingreso")
    fecha_transaccion   = models.DateField(verbose_name="Fecha de Transacción")
    valor               = models.TextField(verbose_name="Valor")
    cuatro_por_mil      = models.TextField(null=True, blank=True)
    observacion         = models.TextField(blank=True, null=True, verbose_name="Observación")

    def __str__(self):
        if self.id_cliente:
            return f"{self.id_cliente.nombre} - {self.valor}"
        return f"Sin Cliente - {self.valor}"

    class Meta:
        verbose_name = "Cargosnodeseado"
        verbose_name_plural = "Cargosnodeseados"
        db_table = "cargosnodeseados"
