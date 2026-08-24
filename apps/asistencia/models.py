"""Control de asistencia de alumnos y docentes vía terminal biométrica o
registro manual, y modelo de datos para el futuro monitoreo de GPS móvil."""
import secrets

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import Plantel, Usuario, Vigencia


class DispositivoBiometrico(models.Model):
    """Terminal biométrica (huella/rostro) instalada en un plantel."""

    plantel = models.ForeignKey(
        Plantel, on_delete=models.PROTECT, related_name="dispositivos_biometricos"
    )
    marca = models.CharField(max_length=100, blank=True)
    modelo = models.CharField(max_length=100, blank=True)
    identificador = models.CharField(
        max_length=50,
        unique=True,
        help_text="Identificador o serie del dispositivo usado por su SDK/API.",
    )
    ubicacion = models.CharField(max_length=150, blank=True)
    activo = models.BooleanField(default=True)
    clave_api = models.CharField(
        max_length=64,
        unique=True,
        editable=False,
        blank=True,
        help_text="Clave secreta generada automáticamente para autenticar a "
        "este dispositivo contra la API REST (header X-Device-Key).",
    )

    class Meta:
        verbose_name = "Dispositivo biométrico"
        verbose_name_plural = "Dispositivos biométricos"
        ordering = ["plantel", "ubicacion"]

    def __str__(self) -> str:
        return f"{self.marca} {self.modelo} ({self.identificador})".strip()

    def save(self, *args, **kwargs):
        if not self.clave_api:
            self.clave_api = secrets.token_hex(32)
        super().save(*args, **kwargs)


class RegistroAsistencia(models.Model):
    """Entrada/salida de un alumno o docente, capturada por un dispositivo
    biométrico o registrada manualmente por un administrativo."""

    class Tipo(models.TextChoices):
        ENTRADA = "ENTRADA", "Entrada"
        SALIDA = "SALIDA", "Salida"

    class Origen(models.TextChoices):
        BIOMETRICO = "BIOMETRICO", "Biométrico"
        MANUAL = "MANUAL", "Manual"

    persona = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="registros_asistencia",
        limit_choices_to={
            "rol_principal__in": [Usuario.Rol.ALUMNO, Usuario.Rol.DOCENTE]
        },
    )
    dispositivo = models.ForeignKey(
        DispositivoBiometrico,
        on_delete=models.SET_NULL,
        related_name="registros",
        null=True,
        blank=True,
    )
    fecha_hora = models.DateTimeField()
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    origen = models.CharField(max_length=10, choices=Origen.choices, default=Origen.BIOMETRICO)
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="registros_asistencia_capturados",
        null=True,
        blank=True,
        help_text="Usuario administrativo que capturó el registro manual.",
    )

    class Meta:
        verbose_name = "Registro de asistencia"
        verbose_name_plural = "Registros de asistencia"
        ordering = ["-fecha_hora"]

    def __str__(self) -> str:
        return f"{self.persona} - {self.get_tipo_display()} ({self.fecha_hora})"

    def clean(self):
        if self.origen == self.Origen.BIOMETRICO and not self.dispositivo_id:
            raise ValidationError(
                "Un registro de origen biométrico debe indicar el dispositivo."
            )
        if self.origen == self.Origen.MANUAL and not self.registrado_por_id:
            raise ValidationError(
                "Un registro manual debe indicar el usuario que lo capturó."
            )


class ParametroGPS(Vigencia):
    """Configuración del intervalo de reporte de ubicación GPS por plantel,
    para la futura app móvil de alumnos/docentes."""

    plantel = models.OneToOneField(
        Plantel, on_delete=models.CASCADE, related_name="parametro_gps"
    )
    intervalo_minutos = models.PositiveSmallIntegerField(
        default=settings.GPS_INTERVALO_DEFAULT_MINUTOS
    )

    class Meta:
        verbose_name = "Parámetro de GPS"
        verbose_name_plural = "Parámetros de GPS"

    def __str__(self) -> str:
        return f"GPS {self.plantel} cada {self.intervalo_minutos} min"

    def clean(self):
        if (
            self.intervalo_minutos is not None
            and self.intervalo_minutos < settings.GPS_INTERVALO_MINIMO_MINUTOS
        ):
            raise ValidationError(
                f"El intervalo mínimo permitido es de "
                f"{settings.GPS_INTERVALO_MINIMO_MINUTOS} minutos."
            )


class UbicacionGPS(models.Model):
    """Punto de ubicación reportado por la app móvil de un alumno o docente."""

    persona = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ubicaciones_gps",
        limit_choices_to={
            "rol_principal__in": [Usuario.Rol.ALUMNO, Usuario.Rol.DOCENTE]
        },
    )
    latitud = models.DecimalField(max_digits=9, decimal_places=6)
    longitud = models.DecimalField(max_digits=9, decimal_places=6)
    timestamp = models.DateTimeField(auto_now_add=True)
    dentro_del_plantel = models.BooleanField(
        default=False,
        help_text="Calculado por el backend al recibir el reporte (geocerca del plantel).",
    )

    class Meta:
        verbose_name = "Ubicación GPS"
        verbose_name_plural = "Ubicaciones GPS"
        ordering = ["-timestamp"]

    def __str__(self) -> str:
        return f"{self.persona} @ ({self.latitud}, {self.longitud}) - {self.timestamp}"
