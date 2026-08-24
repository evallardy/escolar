"""Inscripción/reinscripción de alumnos a un ciclo escolar y a los grupos
(materias) que cursan dentro de ese ciclo."""
from django.core.exceptions import ValidationError
from django.db import models

from apps.academico.models import CicloEscolar, Grupo, Programa
from apps.alumnos.models import Alumno


class Inscripcion(models.Model):
    """Inscripción de un alumno a un programa dentro de un ciclo escolar."""

    class Estatus(models.TextChoices):
        INSCRITO = "INSCRITO", "Inscrito"
        BAJA = "BAJA", "Baja"
        CONCLUIDO = "CONCLUIDO", "Concluido"

    alumno = models.ForeignKey(
        Alumno, on_delete=models.CASCADE, related_name="inscripciones"
    )
    programa = models.ForeignKey(
        Programa, on_delete=models.PROTECT, related_name="inscripciones"
    )
    ciclo_escolar = models.ForeignKey(
        CicloEscolar, on_delete=models.PROTECT, related_name="inscripciones"
    )
    fecha_inscripcion = models.DateField(auto_now_add=True)
    estatus = models.CharField(
        max_length=15, choices=Estatus.choices, default=Estatus.INSCRITO
    )

    class Meta:
        verbose_name = "Inscripción"
        verbose_name_plural = "Inscripciones"
        unique_together = [("alumno", "ciclo_escolar")]
        ordering = ["-ciclo_escolar", "alumno"]

    def __str__(self) -> str:
        return f"{self.alumno} - {self.ciclo_escolar} ({self.get_estatus_display()})"


class InscripcionMateria(models.Model):
    """Grupo (materia) en el que queda inscrito el alumno dentro de una
    inscripción de ciclo. Al concluir el ciclo, esta información se refleja
    en el Cardex del alumno."""

    class Estatus(models.TextChoices):
        INSCRITO = "INSCRITO", "Inscrito"
        BAJA = "BAJA", "Baja de la materia"
        ACREDITADA = "ACREDITADA", "Acreditada"
        NO_ACREDITADA = "NO_ACREDITADA", "No acreditada"

    inscripcion = models.ForeignKey(
        Inscripcion, on_delete=models.CASCADE, related_name="materias"
    )
    grupo = models.ForeignKey(
        Grupo, on_delete=models.PROTECT, related_name="inscripciones_materia"
    )
    calificacion_final = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True
    )
    estatus = models.CharField(
        max_length=15, choices=Estatus.choices, default=Estatus.INSCRITO
    )

    class Meta:
        verbose_name = "Inscripción a materia"
        verbose_name_plural = "Inscripciones a materias"
        unique_together = [("inscripcion", "grupo")]
        ordering = ["inscripcion", "grupo"]

    def __str__(self) -> str:
        return f"{self.inscripcion.alumno} - {self.grupo}"

    def clean(self):
        if self.grupo_id and self.estatus == self.Estatus.INSCRITO:
            ya_inscritos = (
                InscripcionMateria.objects.filter(
                    grupo_id=self.grupo_id, estatus=self.Estatus.INSCRITO
                )
                .exclude(pk=self.pk)
                .count()
            )
            if ya_inscritos >= self.grupo.cupo_maximo:
                raise ValidationError("El grupo ya alcanzó su cupo máximo.")
