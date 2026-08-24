"""Nómina de personal (docente y administrativo) con timbrado fiscal CFDI."""
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models

from apps.core.models import Plantel, Usuario

TAMANO_MAXIMO_ARCHIVO_CFDI_MB = 2


def validar_tamano_archivo_cfdi(archivo):
    limite_bytes = TAMANO_MAXIMO_ARCHIVO_CFDI_MB * 1024 * 1024
    if archivo.size > limite_bytes:
        raise ValidationError(
            f"El archivo no debe superar {TAMANO_MAXIMO_ARCHIVO_CFDI_MB} MB."
        )


class Puesto(models.Model):
    """Puesto/cargo laboral con su sueldo base de referencia."""

    plantel = models.ForeignKey(Plantel, on_delete=models.PROTECT, related_name="puestos")
    nombre = models.CharField(max_length=100)
    sueldo_base = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Puesto"
        verbose_name_plural = "Puestos"
        unique_together = [("plantel", "nombre")]
        ordering = ["plantel", "nombre"]

    def __str__(self) -> str:
        return f"{self.nombre} ({self.plantel})"


class Empleado(models.Model):
    """Perfil de nómina de un docente o administrativo. Complementa (no
    reemplaza) el perfil específico en `docentes.Docente` cuando aplica."""

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil_empleado",
        limit_choices_to={
            "rol_principal__in": [Usuario.Rol.DOCENTE, Usuario.Rol.ADMINISTRATIVO]
        },
    )
    puesto = models.ForeignKey(Puesto, on_delete=models.PROTECT, related_name="empleados")
    rfc = models.CharField("RFC", max_length=13)
    nss = models.CharField("NSS", max_length=15, blank=True)
    fecha_ingreso = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Empleado"
        verbose_name_plural = "Empleados"
        ordering = ["usuario__first_name", "usuario__last_name"]

    def __str__(self) -> str:
        return self.usuario.get_full_name() or self.usuario.username


class PeriodoNomina(models.Model):
    """Periodo de pago (quincena o mes) sobre el que se generan recibos."""

    class Tipo(models.TextChoices):
        QUINCENAL = "QUINCENAL", "Quincenal"
        MENSUAL = "MENSUAL", "Mensual"

    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    cerrado = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Periodo de nómina"
        verbose_name_plural = "Periodos de nómina"
        ordering = ["-fecha_inicio"]

    def __str__(self) -> str:
        return f"{self.get_tipo_display()} {self.fecha_inicio} - {self.fecha_fin}"

    def clean(self):
        if self.fecha_fin and self.fecha_inicio and self.fecha_fin < self.fecha_inicio:
            raise ValidationError(
                "La fecha de fin del periodo no puede ser anterior a la fecha de inicio."
            )


class ReciboNomina(models.Model):
    """Recibo de nómina de un empleado en un periodo, con su estatus de
    timbrado fiscal (CFDI) ante el PAC autorizado por el SAT."""

    class EstatusTimbrado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente de timbrar"
        TIMBRADO = "TIMBRADO", "Timbrado"
        CANCELADO = "CANCELADO", "Cancelado"
        ERROR = "ERROR", "Error de timbrado"

    empleado = models.ForeignKey(
        Empleado, on_delete=models.PROTECT, related_name="recibos"
    )
    periodo = models.ForeignKey(
        PeriodoNomina, on_delete=models.PROTECT, related_name="recibos"
    )
    percepciones = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    deducciones = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    neto = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=Decimal("0.00"))
    estatus_timbrado = models.CharField(
        max_length=10, choices=EstatusTimbrado.choices, default=EstatusTimbrado.PENDIENTE
    )
    uuid_cfdi = models.CharField("UUID CFDI", max_length=36, blank=True)
    archivo_xml = models.FileField(
        upload_to="nomina/cfdi/%Y/%m/",
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(allowed_extensions=["xml"]),
            validar_tamano_archivo_cfdi,
        ],
    )
    archivo_pdf = models.FileField(
        upload_to="nomina/cfdi/%Y/%m/",
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(allowed_extensions=["pdf"]),
            validar_tamano_archivo_cfdi,
        ],
    )

    class Meta:
        verbose_name = "Recibo de nómina"
        verbose_name_plural = "Recibos de nómina"
        unique_together = [("empleado", "periodo")]
        ordering = ["-periodo", "empleado"]

    def __str__(self) -> str:
        return f"{self.empleado} - {self.periodo}"

    def clean(self):
        if self.uuid_cfdi and self.estatus_timbrado != self.EstatusTimbrado.TIMBRADO:
            raise ValidationError(
                "Solo un recibo timbrado puede tener UUID de CFDI."
            )

    def save(self, *args, **kwargs):
        self.neto = (self.percepciones or Decimal("0.00")) - (self.deducciones or Decimal("0.00"))
        super().save(*args, **kwargs)
