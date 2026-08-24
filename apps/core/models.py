"""Modelos base compartidos por todo el proyecto: Plantel, Usuario custom y
el mixin de vigencia que usará toda la parametría (colegiaturas, calendario,
programas, materias, etc.).
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class VigenciaQuerySet(models.QuerySet):
    """Permite filtrar en la base de datos (no solo en Python) los registros
    de parametría vigentes a una fecha dada."""

    def vigentes(self, fecha=None):
        fecha = fecha or timezone.localdate()
        return self.filter(activo=True, vigente_desde__lte=fecha).filter(
            models.Q(vigente_hasta__isnull=True) | models.Q(vigente_hasta__gte=fecha)
        )


class Vigencia(models.Model):
    """Mixin abstracto para parametría con fecha de vigencia.

    Cualquier catálogo que deba conservar historial (colegiaturas, calendario
    escolar, datos de la universidad, materias, programas, etc.) hereda de
    este modelo en lugar de reinventar los campos de vigencia.
    """

    vigente_desde = models.DateField(default=timezone.localdate)
    vigente_hasta = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)

    objects = VigenciaQuerySet.as_manager()

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
    latitud = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        help_text="Coordenada del plantel para calcular la geocerca de GPS.",
    )
    longitud = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        help_text="Coordenada del plantel para calcular la geocerca de GPS.",
    )
    radio_geocerca_metros = models.PositiveIntegerField(
        default=150,
        help_text="Radio (metros) alrededor de latitud/longitud considerado 'dentro del plantel'.",
    )

    class Meta:
        verbose_name = "Plantel"
        verbose_name_plural = "Planteles"
        ordering = ["nombre"]

    def __str__(self) -> str:
        return f"{self.clave} - {self.nombre}"

    def esta_dentro_de_geocerca(self, latitud, longitud) -> bool:
        """Determina si un punto (lat/lon) cae dentro del radio de geocerca
        configurado para este plantel. Si el plantel no tiene coordenadas
        configuradas, no se puede determinar y se considera False."""
        if self.latitud is None or self.longitud is None:
            return False
        return _distancia_haversine_metros(
            float(self.latitud), float(self.longitud), float(latitud), float(longitud)
        ) <= self.radio_geocerca_metros


def _distancia_haversine_metros(lat1, lon1, lat2, lon2) -> float:
    """Distancia en metros entre dos coordenadas geográficas (fórmula de
    Haversine), usada para la geocerca de GPS del plantel."""
    import math

    radio_tierra_m = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radio_tierra_m * c


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
