from django.db             import models
from proveedores.models    import Proveedor
from cotizador.models      import Cotizador
from django.utils.timezone import now

# Create your models here.
class FichaProveedor(models.Model):
    idproveedor         = models.ForeignKey(Proveedor, on_delete=models.CASCADE)
    idcotizador         = models.ForeignKey(Cotizador, on_delete=models.CASCADE)
    comisionproveedor   = models.CharField(max_length=100)
    fechaCreacion       = models.DateTimeField(default=now)

    def __str__(self):
        return self.comisionproveedor


class FichaProveedorPagos(models.Model):
    idproveedor         = models.ForeignKey(Proveedor, on_delete=models.CASCADE)
    pagoProveedor       = models.CharField(max_length=100)
    fechaCreacion       = models.DateTimeField(default=now)

    def __str__(self):
        return self.pagoProveedor
    
