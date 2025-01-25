from django.db import models
from django.utils.timezone import now

class Tramite(models.Model):
    ESTADO_CHOICES = [
        ('Recepción', 'Recepción'),
        ('Validación', 'Validación'),
        ('Ejecución', 'Ejecución'),
        ('Finalización', 'Finalización'),
    ]
    idUsuario       = models.IntegerField()
    idCliente       = models.IntegerField()
    estado = models.CharField(
        max_length=50,
        choices=ESTADO_CHOICES,
        default='Recepción',  # Estado inicial por defecto
    )
    etiquetaUno     = models.CharField(max_length=255, null=True, blank=True)
    etiquetaDos     = models.CharField(max_length=255, null=True, blank=True)
    placa           = models.CharField(max_length=50)
    cilindraje      = models.CharField(max_length=50)
    modelo          = models.CharField(max_length=50)
    chasis          = models.CharField(max_length=50)
    tipoDocumento   = models.CharField(max_length=50)
    numeroDocumento = models.CharField(max_length=50)
    nombreCompleto  = models.CharField(max_length=255)
    telefono        = models.CharField(max_length=20, null=True, blank=True)
    correo          = models.EmailField(null=True, blank=True)
    direccion       = models.TextField(null=True, blank=True)
    pagoInmediato   = models.TextField(null=True, blank=True)
    linkPago        = models.TextField(null=True, blank=True)
    precioDeLey     = models.CharField(max_length=255, default="")  # Por defecto vacío
    comisionPrecioLey = models.CharField(max_length=255, default="")  # Por defecto vacío
    total            = models.CharField(max_length=255, default="")  # Por defecto vacío
    pdf              = models.FileField(upload_to='media/pdfs/', null=True, blank=True)
    fechaCreacion    = models.DateTimeField(default=now)  # Almacena la fecha de creación automáticamente

class LogTramite(models.Model):
    ACCION_CHOICES = [
        ('crear', 'Crear'),
        ('editar', 'Editar'),
        ('eliminar', 'Eliminar'),
    ]
    idTramite   = models.IntegerField()
    idUsuario   = models.IntegerField()
    idCliente   = models.IntegerField()
    accion      = models.CharField(max_length=10, choices=ACCION_CHOICES)
    campo       = models.CharField(max_length=250, null=True, blank=True)
    antiguoValor= models.TextField()
    nuevoValor  = models.TextField()
    fecha       = models.DateTimeField(auto_now_add=True)