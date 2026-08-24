"""Tareas asignadas por docentes a un grupo y las entregas de los alumnos."""
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone

from apps.academico.models import Grupo
from apps.alumnos.models import Alumno
from apps.docentes.models import Docente

EXTENSIONES_ENTREGA_PERMITIDAS = [
    "pdf",
    "doc",
    "docx",
    "xls",
    "xlsx",
    "ppt",
    "pptx",
    "zip",
    "jpg",
    "jpeg",
    "png",
]
TAMANO_MAXIMO_ENTREGA_MB = 20


def validar_tamano_entrega(archivo):
    limite_bytes = TAMANO_MAXIMO_ENTREGA_MB * 1024 * 1024
    if archivo.size > limite_bytes:
        raise ValidationError(
            f"El archivo no debe superar {TAMANO_MAXIMO_ENTREGA_MB} MB."
        )


class Tarea(models.Model):
    """Tarea/actividad asignada por un docente a un grupo."""

    grupo = models.ForeignKey(Grupo, on_delete=models.CASCADE, related_name="tareas")
    docente = models.ForeignKey(
        Docente, on_delete=models.PROTECT, related_name="tareas"
    )
    titulo = models.CharField(max_length=200)
    instrucciones = models.TextField(blank=True)
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    fecha_entrega = models.DateTimeField()
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Tarea"
        verbose_name_plural = "Tareas"
        ordering = ["-fecha_entrega"]

    def __str__(self) -> str:
        return f"{self.titulo} - {self.grupo}"

    def clean(self):
        if self.pk is None and self.fecha_entrega and self.fecha_entrega < timezone.now():
            raise ValidationError(
                "La fecha de entrega de una tarea nueva no puede ser en el pasado."
            )


class EntregaTrabajo(models.Model):
    """Entrega de un alumno para una tarea, con calificación y comentarios
    del docente."""

    tarea = models.ForeignKey(Tarea, on_delete=models.CASCADE, related_name="entregas")
    alumno = models.ForeignKey(
        Alumno, on_delete=models.CASCADE, related_name="entregas_trabajo"
    )
    archivo = models.FileField(
        upload_to="trabajos/entregas/%Y/%m/",
        validators=[
            FileExtensionValidator(allowed_extensions=EXTENSIONES_ENTREGA_PERMITIDAS),
            validar_tamano_entrega,
        ],
    )
    fecha_entrega = models.DateTimeField(auto_now_add=True)
    calificacion = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True
    )
    comentarios = models.TextField(blank=True)

    class Meta:
        verbose_name = "Entrega de trabajo"
        verbose_name_plural = "Entregas de trabajo"
        unique_together = [("tarea", "alumno")]
        ordering = ["-fecha_entrega"]

    def __str__(self) -> str:
        return f"{self.alumno} - {self.tarea}"

    @property
    def entregado_tarde(self) -> bool:
        if not self.fecha_entrega or not self.tarea.fecha_entrega:
            return False
        return self.fecha_entrega > self.tarea.fecha_entrega
