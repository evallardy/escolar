"""Catálogos académicos: niveles educativos, programas, planes de estudio,
materias, ciclos escolares y calendario. Todo lo parametrizable hereda de
``Vigencia`` (vigente_desde/vigente_hasta/activo) para conservar historial.
"""
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import Plantel, Vigencia


class NivelEducativo(Vigencia):
    """Preparatoria, Licenciatura, Maestría, Doctorado, etc. (catálogo abierto)."""

    clave = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100)
    orden = models.PositiveSmallIntegerField(
        default=0, help_text="Orden de despliegue (menor primero)."
    )

    class Meta:
        verbose_name = "Nivel educativo"
        verbose_name_plural = "Niveles educativos"
        ordering = ["orden", "nombre"]

    def __str__(self) -> str:
        return self.nombre


class Programa(Vigencia):
    """Un programa académico ofrecido por un plantel (ej. "Ingeniería en
    Sistemas", "Bachillerato General", "Maestría en Administración")."""

    class Modalidad(models.TextChoices):
        PRESENCIAL = "PRESENCIAL", "Presencial"
        EN_LINEA = "EN_LINEA", "En línea"
        MIXTA = "MIXTA", "Mixta"

    clave = models.CharField(max_length=20)
    nombre = models.CharField(max_length=150)
    nivel = models.ForeignKey(
        NivelEducativo, on_delete=models.PROTECT, related_name="programas"
    )
    plantel = models.ForeignKey(
        Plantel, on_delete=models.PROTECT, related_name="programas"
    )
    modalidad = models.CharField(
        max_length=15, choices=Modalidad.choices, default=Modalidad.PRESENCIAL
    )
    duracion_periodos = models.PositiveSmallIntegerField(
        help_text="Número de periodos (semestres/cuatrimestres/años) del programa."
    )
    titulo_otorga = models.CharField(
        max_length=150, blank=True, help_text="Título/grado que otorga al egresar."
    )

    class Meta:
        verbose_name = "Programa"
        verbose_name_plural = "Programas"
        unique_together = [("clave", "plantel")]
        ordering = ["nivel__orden", "nombre"]

    def __str__(self) -> str:
        return f"{self.nombre} ({self.nivel})"


class PlanEstudios(Vigencia):
    """Versión de un plan de estudios de un programa (permite tener varias
    generaciones vigentes/históricas del mismo programa)."""

    programa = models.ForeignKey(
        Programa, on_delete=models.CASCADE, related_name="planes_estudio"
    )
    version = models.CharField(
        max_length=20, help_text='Ej. "2024", "2024-2".'
    )
    total_creditos = models.PositiveSmallIntegerField(default=0)
    observaciones = models.TextField(blank=True)

    class Meta:
        verbose_name = "Plan de estudios"
        verbose_name_plural = "Planes de estudio"
        unique_together = [("programa", "version")]
        ordering = ["programa", "-version"]

    def __str__(self) -> str:
        return f"{self.programa} - Plan {self.version}"


class Materia(Vigencia):
    """Materia/asignatura perteneciente a un plan de estudios."""

    class Tipo(models.TextChoices):
        OBLIGATORIA = "OBLIGATORIA", "Obligatoria"
        OPTATIVA = "OPTATIVA", "Optativa"

    plan_estudios = models.ForeignKey(
        PlanEstudios, on_delete=models.CASCADE, related_name="materias"
    )
    clave = models.CharField(max_length=20)
    nombre = models.CharField(max_length=150)
    periodo = models.PositiveSmallIntegerField(
        help_text="Semestre/cuatrimestre dentro del plan al que pertenece."
    )
    creditos = models.PositiveSmallIntegerField(default=0)
    horas_teoricas = models.PositiveSmallIntegerField(default=0)
    horas_practicas = models.PositiveSmallIntegerField(default=0)
    tipo = models.CharField(
        max_length=15, choices=Tipo.choices, default=Tipo.OBLIGATORIA
    )
    seriacion = models.ManyToManyField(
        "self",
        symmetrical=False,
        blank=True,
        related_name="materias_posteriores",
        help_text="Materias que se requieren cursar/aprobar antes que esta.",
    )

    class Meta:
        verbose_name = "Materia"
        verbose_name_plural = "Materias"
        unique_together = [("plan_estudios", "clave")]
        ordering = ["plan_estudios", "periodo", "nombre"]

    def __str__(self) -> str:
        return f"{self.clave} - {self.nombre}"


class CicloEscolar(models.Model):
    """Periodo escolar (ej. "2026-2027", "Enero-Abril 2026") de un plantel."""

    plantel = models.ForeignKey(
        Plantel, on_delete=models.PROTECT, related_name="ciclos_escolares"
    )
    clave = models.CharField(max_length=20)
    nombre = models.CharField(max_length=100)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    activo = models.BooleanField(
        default=True, help_text="Ciclo en curso actualmente para este plantel."
    )

    class Meta:
        verbose_name = "Ciclo escolar"
        verbose_name_plural = "Ciclos escolares"
        unique_together = [("plantel", "clave")]
        ordering = ["-fecha_inicio"]

    def __str__(self) -> str:
        return f"{self.nombre} ({self.plantel.clave})"

    def clean(self):
        if self.fecha_inicio and self.fecha_fin and self.fecha_fin <= self.fecha_inicio:
            raise ValidationError(
                "La fecha de fin del ciclo escolar debe ser posterior a la fecha de inicio."
            )


class CalendarioEvento(models.Model):
    """Evento del calendario escolar: días de clase, vacaciones, exámenes,
    suspensiones, periodos de inscripción, etc."""

    class Tipo(models.TextChoices):
        CLASES = "CLASES", "Día de clases"
        VACACIONES = "VACACIONES", "Vacaciones"
        EXAMEN = "EXAMEN", "Periodo de exámenes"
        SUSPENSION = "SUSPENSION", "Suspensión de labores"
        INSCRIPCION = "INSCRIPCION", "Periodo de inscripción/reinscripción"
        OTRO = "OTRO", "Otro"

    ciclo_escolar = models.ForeignKey(
        CicloEscolar, on_delete=models.CASCADE, related_name="eventos"
    )
    nombre = models.CharField(max_length=150)
    tipo = models.CharField(max_length=15, choices=Tipo.choices)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(
        null=True, blank=True, help_text="Vacío si es un evento de un solo día."
    )
    descripcion = models.TextField(blank=True)

    class Meta:
        verbose_name = "Evento de calendario"
        verbose_name_plural = "Eventos de calendario"
        ordering = ["fecha_inicio"]

    def __str__(self) -> str:
        return f"{self.nombre} ({self.fecha_inicio})"

    def clean(self):
        if self.fecha_fin and self.fecha_fin < self.fecha_inicio:
            raise ValidationError(
                "La fecha de fin del evento no puede ser anterior a la fecha de inicio."
            )
