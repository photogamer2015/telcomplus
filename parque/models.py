import uuid

from django.conf import settings
from django.db import models
from django.urls import reverse


class Equipo(models.Model):
    IMPRESORA = 'IMPRESORA'
    LAPTOP = 'LAPTOP'
    PANTALLA = 'PANTALLA'
    OTRO = 'OTRO'

    TIPO_CHOICES = [
        (IMPRESORA, 'Impresora'),
        (LAPTOP, 'Laptop'),
        (PANTALLA, 'Pantalla'),
        (OTRO, 'Otro'),
    ]

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES)
    marca = models.CharField(max_length=80)
    modelo = models.CharField(max_length=100)
    serie = models.CharField(max_length=100, unique=True)
    empresa_atencion = models.CharField(max_length=120, blank=True)
    razon_social_cliente = models.CharField(max_length=160, blank=True)
    provincia = models.CharField(max_length=80, blank=True)
    ciudad = models.CharField(max_length=80, blank=True)
    direccion = models.TextField(blank=True)
    area_departamento = models.CharField(max_length=120, blank=True)
    ubicacion_coordenadas = models.URLField(blank=True)
    qr_code = models.ImageField(upload_to='qr_equipos/', blank=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='equipos_creados',
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['tipo', 'marca', 'modelo']
        verbose_name = 'equipo'
        verbose_name_plural = 'equipos'

    def __str__(self):
        return f'{self.tipo} {self.marca} {self.modelo} - {self.serie}'

    def public_path(self):
        return reverse('public_report', kwargs={'public_id': self.public_id})

    def public_url(self, base_url='http://127.0.0.1:8000'):
        return f'{base_url.rstrip("/")}{self.public_path()}'


class TicketSoporte(models.Model):
    NUEVO = 'NUEVO'
    EN_REVISION = 'EN_REVISION'
    RESUELTO = 'RESUELTO'

    ESTADO_CHOICES = [
        (NUEVO, 'En Proceso'),
        (EN_REVISION, 'En Reparación'),
        (RESUELTO, 'Resuelto'),
    ]

    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='tickets')
    nombre_cliente = models.CharField(max_length=120)
    telefono = models.CharField(max_length=40)
    empresa = models.CharField(max_length=140)
    problema = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default=NUEVO)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-creado_en']
        verbose_name = 'ticket de soporte'
        verbose_name_plural = 'tickets de soporte'

    def __str__(self):
        return f'Ticket #{self.pk} - {self.equipo.serie}'

# Create your models here.
