"""Docentes y su asignación a los grupos de clase."""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.academico.models import Grupo
from apps.core.models import Plantel, Usuario


class Docente(models.Model):
    """Perfil docente ligado 1 a 1 con un Usuario de rol DOCENTE."""

    class NivelEstudios(models.TextChoices):
        LICENCIATURA = "LICENCIATURA", "Licenciatura"
        MAESTRIA = "MAESTRIA", "Maestría"
        DOCTORADO = "DOCTORADO", "Doctorado"

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil_docente",
        limit_choices_to={"rol_principal": Usuario.Rol.DOCENTE},
    )
    planteles = models.ManyToManyField(Plantel, related_name="docentes", blank=True)
    numero_empleado = models.CharField(max_length=20, unique=True)
    especialidad = models.CharField(max_length=150, blank=True)
    nivel_estudios = models.CharField(
        max_length=15, choices=NivelEstudios.choices, blank=True
    )
    rfc = models.CharField("RFC", max_length=13, blank=True)
    curp = models.CharField("CURP", max_length=18, blank=True)
    cedula_profesional = models.CharField(max_length=20, blank=True)
    fecha_ingreso = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Docente"
        verbose_name_plural = "Docentes"
        ordering = ["usuario__first_name", "usuario__last_name"]

    def __str__(self) -> str:
        return self.usuario.get_full_name() or self.usuario.username


class AsignacionDocente(models.Model):
    """Asignación de un docente a un grupo. Se conserva historial: si el
    docente cambia a mitad de ciclo, la asignación anterior se marca
    ``activo=False`` en lugar de borrarla."""

    docente = models.ForeignKey(
        Docente, on_delete=models.PROTECT, related_name="asignaciones"
    )
    grupo = models.ForeignKey(
        Grupo, on_delete=models.CASCADE, related_name="asignaciones_docente"
    )
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Asignación de docente"
        verbose_name_plural = "Asignaciones de docente"
        ordering = ["-fecha_inicio"]

    def __str__(self) -> str:
        return f"{self.docente} -> {self.grupo}"

    def clean(self):
        if self.activo:
            existe_otra_activa = (
                AsignacionDocente.objects.filter(grupo=self.grupo, activo=True)
                .exclude(pk=self.pk)
                .exists()
            )
            if existe_otra_activa:
                raise ValidationError(
                    "Ya existe una asignación de docente activa para este grupo. "
                    "Marca la anterior como inactiva antes de agregar una nueva."
                )
