# cuentas_bancarias/models.py
from django.db import models

class CuentaBancaria(models.Model):
    idCotizador         = models.IntegerField()
    idBanco             = models.IntegerField()
    fechaIngreso        = models.DateTimeField(auto_now_add=True)
    fechaTransaccion    = models.CharField(max_length=250)
    descripcion         = models.TextField(null=True, blank=True)
    valor               = models.TextField(null=True, blank=True)
    cuatro_por_mil      = models.TextField(null=True, blank=True)
    cilindraje          = models.TextField(null=True, blank=True)
    nombreTitular       = models.TextField(null=True, blank=True)
    image               = models.ImageField(upload_to='comprobantesdepago/', null=True, blank=True)
    
    def __str__(self):
        return f"{self.nombreTitular} ({self.cilindraje})"
