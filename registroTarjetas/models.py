# cuentas_bancarias/models.py
from django.db import models

class RegistroTarjetas(models.Model):
    numero_cuenta = models.CharField(max_length=40, unique=True)
    nombre_cuenta = models.CharField(max_length=250)
    descripcion   = models.TextField(null=True, blank=True)
    saldo         = models.TextField(null=True, blank=True)
    imagen        = models.ImageField(upload_to='tarjetas/', null=True, blank=True)
    banco         = models.TextField(null=True, blank=True)
    is_daviplata  = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.nombre_cuenta} ({self.numero_cuenta})"
    
    class Meta:
        db_table = "registrotarjetas_registrotarjetas"

