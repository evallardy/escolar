"""Conceptos de cobro (colegiaturas, inscripción, exámenes, etc.), cargos
generados a los alumnos, pagos (manuales o vía pasarela) y becas/descuentos."""
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.academico.models import CicloEscolar, Programa
from apps.alumnos.models import Alumno
from apps.core.models import Plantel, Vigencia


class ConceptoCobro(Vigencia):
    """Definición parametrizable de un concepto de cobro (ej. "Colegiatura
    Prepa 2025-2026") con su periodicidad y monto vigente."""

    class Periodicidad(models.TextChoices):
        UNICO = "UNICO", "Pago único"
        MENSUAL = "MENSUAL", "Mensual"
        BIMESTRAL = "BIMESTRAL", "Bimestral"
        TRIMESTRAL = "TRIMESTRAL", "Trimestral"
        CUATRIMESTRAL = "CUATRIMESTRAL", "Cuatrimestral"
        SEMESTRAL = "SEMESTRAL", "Semestral"
        ANUAL = "ANUAL", "Anual"

    plantel = models.ForeignKey(
        Plantel, on_delete=models.PROTECT, related_name="conceptos_cobro"
    )
    programa = models.ForeignKey(
        Programa,
        on_delete=models.PROTECT,
        related_name="conceptos_cobro",
        null=True,
        blank=True,
        help_text="Vacío si el concepto aplica a todos los programas del plantel.",
    )
    nombre = models.CharField(max_length=150)
    periodicidad = models.CharField(max_length=15, choices=Periodicidad.choices)
    monto = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Concepto de cobro"
        verbose_name_plural = "Conceptos de cobro"
        ordering = ["plantel", "nombre"]

    def __str__(self) -> str:
        return f"{self.nombre} (${self.monto})"


class CargoAlumno(models.Model):
    """Cargo/adeudo generado a un alumno a partir de un concepto de cobro
    (ej. la mensualidad de octubre del ciclo 2025-2026)."""

    class Estatus(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        PAGADO = "PAGADO", "Pagado"
        VENCIDO = "VENCIDO", "Vencido"
        CANCELADO = "CANCELADO", "Cancelado"

    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name="cargos")
    concepto = models.ForeignKey(
        ConceptoCobro, on_delete=models.PROTECT, related_name="cargos"
    )
    ciclo_escolar = models.ForeignKey(
        CicloEscolar, on_delete=models.PROTECT, related_name="cargos"
    )
    periodo_etiqueta = models.CharField(
        max_length=50,
        blank=True,
        help_text='Ej. "Mensualidad 3/10", "Inscripción 2025-2026".',
    )
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_limite = models.DateField()
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    estatus = models.CharField(
        max_length=15, choices=Estatus.choices, default=Estatus.PENDIENTE
    )

    class Meta:
        verbose_name = "Cargo de alumno"
        verbose_name_plural = "Cargos de alumnos"
        ordering = ["-fecha_limite"]

    def __str__(self) -> str:
        return f"{self.alumno} - {self.concepto.nombre} (${self.monto})"

    @property
    def monto_pagado(self) -> Decimal:
        total = self.pagos.aggregate(total=models.Sum("monto"))["total"]
        return total or Decimal("0.00")

    @property
    def saldo_pendiente(self) -> Decimal:
        return self.monto - self.monto_pagado

    def refrescar_estatus(self, guardar: bool = True) -> None:
        """Recalcula el estatus del cargo según lo pagado y la fecha límite."""
        if self.estatus == self.Estatus.CANCELADO:
            return
        if self.saldo_pendiente <= 0:
            self.estatus = self.Estatus.PAGADO
        elif self.fecha_limite and self.fecha_limite < timezone.localdate():
            self.estatus = self.Estatus.VENCIDO
        else:
            self.estatus = self.Estatus.PENDIENTE
        if guardar:
            self.save(update_fields=["estatus"])


class Pago(models.Model):
    """Pago aplicado a un cargo, ya sea capturado manualmente por
    administración o recibido vía pasarela de pago en línea."""

    class FormaPago(models.TextChoices):
        EFECTIVO = "EFECTIVO", "Efectivo"
        TRANSFERENCIA = "TRANSFERENCIA", "Transferencia"
        TARJETA = "TARJETA", "Tarjeta"
        CHEQUE = "CHEQUE", "Cheque"

    class Origen(models.TextChoices):
        MANUAL = "MANUAL", "Registro manual"
        PASARELA = "PASARELA", "Pasarela de pago en línea"

    cargo = models.ForeignKey(CargoAlumno, on_delete=models.PROTECT, related_name="pagos")
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_pago = models.DateField()
    fecha_registro = models.DateTimeField(auto_now_add=True)
    forma_pago = models.CharField(max_length=15, choices=FormaPago.choices)
    origen = models.CharField(
        max_length=10, choices=Origen.choices, default=Origen.MANUAL
    )
    referencia_transaccion = models.CharField(max_length=100, blank=True)
    capturado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="pagos_capturados",
        null=True,
        blank=True,
        help_text="Usuario administrativo que capturó el pago manual (vacío si vino de la pasarela).",
    )

    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        ordering = ["-fecha_pago"]

    def __str__(self) -> str:
        return f"Pago ${self.monto} - {self.cargo}"

    def clean(self):
        if self.monto is not None and self.monto <= 0:
            raise ValidationError("El monto del pago debe ser mayor a cero.")
        if self.cargo_id:
            saldo_previo = self.cargo.saldo_pendiente
            if self.pk:
                saldo_previo += Pago.objects.get(pk=self.pk).monto
            if self.monto and self.monto > saldo_previo:
                raise ValidationError(
                    "El monto del pago excede el saldo pendiente del cargo."
                )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.cargo.refrescar_estatus()

    def delete(self, *args, **kwargs):
        cargo = self.cargo
        super().delete(*args, **kwargs)
        cargo.refrescar_estatus()


class Beca(Vigencia):
    """Beca o descuento aplicable a un alumno, ya sea como porcentaje o
    monto fijo, sobre un concepto específico o sobre todos sus cargos."""

    class TipoDescuento(models.TextChoices):
        PORCENTAJE = "PORCENTAJE", "Porcentaje"
        MONTO_FIJO = "MONTO_FIJO", "Monto fijo"

    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name="becas")
    concepto = models.ForeignKey(
        ConceptoCobro,
        on_delete=models.PROTECT,
        related_name="becas",
        null=True,
        blank=True,
        help_text="Vacío si la beca aplica a todos los conceptos del alumno.",
    )
    tipo = models.CharField(max_length=12, choices=TipoDescuento.choices)
    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Porcentaje (0-100) o monto fijo, según el tipo.",
    )
    motivo = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Beca / descuento"
        verbose_name_plural = "Becas / descuentos"
        ordering = ["alumno"]

    def __str__(self) -> str:
        valor_str = f"{self.valor}%" if self.tipo == self.TipoDescuento.PORCENTAJE else f"${self.valor}"
        return f"{self.alumno} - {valor_str}"

    def clean(self):
        if self.tipo == self.TipoDescuento.PORCENTAJE and self.valor is not None:
            if not (Decimal("0") <= self.valor <= Decimal("100")):
                raise ValidationError("El porcentaje de la beca debe estar entre 0 y 100.")
