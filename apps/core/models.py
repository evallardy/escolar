"""Modelos base compartidos por todo el proyecto: Plantel, Usuario custom y
el mixin de vigencia que usará toda la parametría (colegiaturas, calendario,
programas, materias, etc.).
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class Vigencia(models.Model):
    """Mixin abstracto para parametría con fecha de vigencia.

    Cualquier catálogo que deba conservar historial (colegiaturas, calendario
    escolar, datos de la universidad, materias, programas, etc.) hereda de
    este modelo en lugar de reinventar los campos de vigencia.
    """

    vigente_desde = models.DateField(default=timezone.localdate)
    vigente_hasta = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        abstract = True

    @property
    def esta_vigente(self) -> bool:
        hoy = timezone.localdate()
        if not self.activo:
            return False
        if self.vigente_hasta and hoy > self.vigente_hasta:
            return False
        return hoy >= self.vigente_desde


class Plantel(models.Model):
    """Campus/sede de la institución (soporte multi-plantel)."""

    clave = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=150)
    razon_social = models.CharField(max_length=200, blank=True)
    rfc = models.CharField("RFC", max_length=13, blank=True)
    direccion = models.CharField(max_length=255, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    logo = models.ImageField(upload_to="planteles/logos/", null=True, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Plantel"
        verbose_name_plural = "Planteles"
        ordering = ["nombre"]

    def __str__(self) -> str:
        return f"{self.clave} - {self.nombre}"


class Usuario(AbstractUser):
    """Usuario del sistema. El rol determina el portal/dashboard al entrar."""

    class Rol(models.TextChoices):
        PADRE = "PADRE", "Padre/Tutor"
        ALUMNO = "ALUMNO", "Alumno"
        DOCENTE = "DOCENTE", "Docente"
        ADMINISTRATIVO = "ADMINISTRATIVO", "Administrativo"
        DIRECTIVO = "DIRECTIVO", "Directivo"

    rol_principal = models.CharField(max_length=20, choices=Rol.choices)
    planteles = models.ManyToManyField(
        Plantel, blank=True, related_name="usuarios",
        help_text="Planteles a los que tiene acceso este usuario.",
    )
    telefono = models.CharField(max_length=20, blank=True)
    foto = models.ImageField(upload_to="usuarios/fotos/", null=True, blank=True)

    def __str__(self) -> str:
        return self.get_full_name() or self.username

    def dashboard_url_name(self) -> str:
        """Nombre de la URL del dashboard correspondiente a su rol."""
        return {
            self.Rol.PADRE: "portal:dashboard_padres",
            self.Rol.ALUMNO: "portal:dashboard_alumnos",
            self.Rol.DOCENTE: "portal:dashboard_docentes",
            self.Rol.ADMINISTRATIVO: "portal:dashboard_administrativos",
            self.Rol.DIRECTIVO: "portal:dashboard_directivos",
        }.get(self.rol_principal, "portal:dashboard_generico")
