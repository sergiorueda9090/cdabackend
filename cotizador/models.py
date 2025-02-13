from django.db import models
from django.utils.timezone import now

class Cotizador(models.Model):
    idUsuario       = models.IntegerField()
    idCliente       = models.IntegerField()
    etiquetaDos     = models.CharField(max_length=255, null=True, blank=True)
    idEtiqueta      = models.IntegerField()
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
    archivo          = models.ImageField(upload_to='cotizador_confirm_price/', null=True, blank=True)  # Imagen opcional
    fechaCreacion    = models.DateTimeField(default=now)  # Almacena la fecha de creación automáticamente
    cotizadorModulo             = models.CharField(max_length=1, default="1")  # Por defecto 1
    tramiteModulo               = models.CharField(max_length=1, default="0")  # Por defecto 0
    confirmacionPreciosModulo   = models.CharField(max_length=1, default="0")  # Por defecto 0
    pdfsModulo                  = models.CharField(max_length=1, default="0")  # Por defecto 0
    idBanco         = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"Cotizador {self.id} - {self.nombreCompleto}"


class LogCotizador(models.Model):
    ACCION_CHOICES = [
        ('crear', 'Crear'),
        ('editar', 'Editar'),
        ('eliminar', 'Eliminar'),
    ]
    idCotizador   = models.IntegerField()
    idUsuario     = models.IntegerField()
    idCliente     = models.IntegerField()
    accion        = models.CharField(max_length=10, choices=ACCION_CHOICES)
    campo         = models.CharField(max_length=250, null=True, blank=True)
    antiguoValor  = models.TextField()
    nuevoValor    = models.TextField()
    fecha         = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Log {self.id} - Accion: {self.accion}"
