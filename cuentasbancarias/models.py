# cuentas_bancarias/models.py
from django.db import models

class CuentaBancaria(models.Model):
    numero_cuenta = models.CharField(max_length=40, unique=True)
    nombre_cuenta = models.CharField(max_length=250)
    descripcion = models.TextField(null=True, blank=True)
    saldo = models.TextField()
    imagen = models.ImageField(upload_to='cuentas/', null=True, blank=True)
    
    def __str__(self):
        return f"{self.nombre_cuenta} ({self.numero_cuenta})"
