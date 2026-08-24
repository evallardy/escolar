"""Registro de incidencias (conductuales, académicas, administrativas) de
alumnos, docentes o personal, con bitácora de seguimiento."""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models

from apps.core.models import Vigencia

EXTENSIONES_ADJUNTO_PERMITIDAS = ["pdf", "jpg", "jpeg", "png"]
TAMANO_MAXIMO_ADJUNTO_MB = 5


def validar_tamano_adjunto(archivo):
    limite_bytes = TAMANO_MAXIMO_ADJUNTO_MB * 1024 * 1024
    if archivo.size > limite_bytes:
        raise ValidationError(
            f"El archivo no debe superar {TAMANO_MAXIMO_ADJUNTO_MB} MB."
        )


class TipoIncidencia(Vigencia):
    """Catálogo de tipos de incidencia (ej. "Falta de respeto", "Retardo
    reiterado", "Accidente"), con su nivel de gravedad."""

    class Gravedad(models.TextChoices):
        LEVE = "LEVE", "Leve"
        MODERADA = "MODERADA", "Moderada"
        GRAVE = "GRAVE", "Grave"

    clave = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=150)
    gravedad = models.CharField(max_length=10, choices=Gravedad.choices)

    class Meta:
        verbose_name = "Tipo de incidencia"
        verbose_name_plural = "Tipos de incidencia"
        ordering = ["nombre"]

    def __str__(self) -> str:
        return f"{self.nombre} ({self.get_gravedad_display()})"


class Incidencia(models.Model):
    """Incidencia registrada sobre una persona (alumno, docente o
    administrativo) dentro del plantel."""

    class Estatus(models.TextChoices):
        ABIERTA = "ABIERTA", "Abierta"
        EN_SEGUIMIENTO = "EN_SEGUIMIENTO", "En seguimiento"
        CERRADA = "CERRADA", "Cerrada"

    persona_involucrada = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="incidencias_involucrado",
    )
    tipo = models.ForeignKey(
        TipoIncidencia, on_delete=models.PROTECT, related_name="incidencias"
    )
    descripcion = models.TextField()
    fecha = models.DateTimeField()
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="incidencias_registradas",
        null=True,
    )
    estatus = models.CharField(
        max_length=20, choices=Estatus.choices, default=Estatus.ABIERTA
    )
    adjunto = models.FileField(
        upload_to="incidencias/adjuntos/%Y/%m/",
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(allowed_extensions=EXTENSIONES_ADJUNTO_PERMITIDAS),
            validar_tamano_adjunto,
        ],
    )

    class Meta:
        verbose_name = "Incidencia"
        verbose_name_plural = "Incidencias"
        ordering = ["-fecha"]

    def __str__(self) -> str:
        return f"{self.persona_involucrada} - {self.tipo} ({self.fecha:%Y-%m-%d})"


class SeguimientoIncidencia(models.Model):
    """Entrada de bitácora/escalamiento sobre una incidencia."""

    incidencia = models.ForeignKey(
        Incidencia, on_delete=models.CASCADE, related_name="seguimientos"
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    comentario = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Seguimiento de incidencia"
        verbose_name_plural = "Seguimientos de incidencia"
        ordering = ["fecha"]

    def __str__(self) -> str:
        return f"Seguimiento de {self.incidencia} - {self.fecha:%Y-%m-%d %H:%M}"
