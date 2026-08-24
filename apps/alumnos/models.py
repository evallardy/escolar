"""Alumnos, tutores/padres, cardex (historial académico) y expediente
documental."""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models

from apps.academico.models import CicloEscolar, Grupo, Materia, PlanEstudios, Programa
from apps.core.models import Plantel, Usuario

EXTENSIONES_DOCUMENTOS_PERMITIDAS = ["pdf", "jpg", "jpeg", "png"]
TAMANO_MAXIMO_DOCUMENTO_MB = 5


def validar_tamano_documento(archivo):
    limite_bytes = TAMANO_MAXIMO_DOCUMENTO_MB * 1024 * 1024
    if archivo.size > limite_bytes:
        raise ValidationError(
            f"El archivo no debe superar {TAMANO_MAXIMO_DOCUMENTO_MB} MB."
        )


class Alumno(models.Model):
    """Perfil de alumno ligado 1 a 1 con un Usuario de rol ALUMNO."""

    class Estatus(models.TextChoices):
        ACTIVO = "ACTIVO", "Activo"
        BAJA_TEMPORAL = "BAJA_TEMPORAL", "Baja temporal"
        BAJA_DEFINITIVA = "BAJA_DEFINITIVA", "Baja definitiva"
        EGRESADO = "EGRESADO", "Egresado"
        TITULADO = "TITULADO", "Titulado"

    class Sexo(models.TextChoices):
        MUJER = "M", "Mujer"
        HOMBRE = "H", "Hombre"
        OTRO = "O", "Otro"

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil_alumno",
        limit_choices_to={"rol_principal": Usuario.Rol.ALUMNO},
    )
    matricula = models.CharField(max_length=20, unique=True)
    plantel = models.ForeignKey(Plantel, on_delete=models.PROTECT, related_name="alumnos")
    programa = models.ForeignKey(
        Programa, on_delete=models.PROTECT, related_name="alumnos"
    )
    plan_estudios = models.ForeignKey(
        PlanEstudios,
        on_delete=models.PROTECT,
        related_name="alumnos",
        null=True,
        blank=True,
    )
    estatus = models.CharField(
        max_length=20, choices=Estatus.choices, default=Estatus.ACTIVO
    )
    fecha_ingreso = models.DateField(null=True, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    sexo = models.CharField(max_length=1, choices=Sexo.choices, blank=True)
    curp = models.CharField("CURP", max_length=18, blank=True)
    direccion = models.CharField(max_length=255, blank=True)
    contacto_emergencia = models.CharField(max_length=150, blank=True)
    telefono_emergencia = models.CharField(max_length=20, blank=True)

    class Meta:
        verbose_name = "Alumno"
        verbose_name_plural = "Alumnos"
        ordering = ["usuario__first_name", "usuario__last_name"]

    def __str__(self) -> str:
        nombre = self.usuario.get_full_name() or self.usuario.username
        return f"{self.matricula} - {nombre}"


class Tutor(models.Model):
    """Perfil de padre/tutor ligado 1 a 1 con un Usuario de rol PADRE."""

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil_tutor",
        limit_choices_to={"rol_principal": Usuario.Rol.PADRE},
    )
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.CharField(max_length=255, blank=True)
    ocupacion = models.CharField(max_length=100, blank=True)
    alumnos = models.ManyToManyField(
        Alumno, through="AlumnoTutor", related_name="tutores"
    )

    class Meta:
        verbose_name = "Tutor"
        verbose_name_plural = "Tutores"

    def __str__(self) -> str:
        return self.usuario.get_full_name() or self.usuario.username


class AlumnoTutor(models.Model):
    """Relación alumno-tutor con el parentesco."""

    class Parentesco(models.TextChoices):
        PADRE = "PADRE", "Padre"
        MADRE = "MADRE", "Madre"
        TUTOR_LEGAL = "TUTOR_LEGAL", "Tutor legal"
        OTRO = "OTRO", "Otro"

    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE)
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE)
    parentesco = models.CharField(max_length=15, choices=Parentesco.choices)
    es_contacto_principal = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Relación alumno-tutor"
        verbose_name_plural = "Relaciones alumno-tutor"
        unique_together = [("alumno", "tutor")]

    def __str__(self) -> str:
        return f"{self.tutor} ({self.get_parentesco_display()}) de {self.alumno}"


class Cardex(models.Model):
    """Historial académico del alumno: registro definitivo de cada materia
    cursada, su calificación final y estatus."""

    class Estatus(models.TextChoices):
        CURSANDO = "CURSANDO", "Cursando"
        APROBADA = "APROBADA", "Aprobada"
        REPROBADA = "REPROBADA", "Reprobada"
        BAJA = "BAJA", "Baja de la materia"

    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE, related_name="cardex")
    materia = models.ForeignKey(Materia, on_delete=models.PROTECT, related_name="cardex")
    grupo = models.ForeignKey(
        Grupo, on_delete=models.SET_NULL, related_name="cardex", null=True, blank=True
    )
    ciclo_escolar = models.ForeignKey(
        CicloEscolar, on_delete=models.PROTECT, related_name="cardex"
    )
    calificacion = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True
    )
    estatus = models.CharField(
        max_length=15, choices=Estatus.choices, default=Estatus.CURSANDO
    )
    creditos_obtenidos = models.PositiveSmallIntegerField(default=0)
    intento = models.PositiveSmallIntegerField(
        default=1, help_text="Número de vez que cursa la materia."
    )

    class Meta:
        verbose_name = "Registro de cardex"
        verbose_name_plural = "Cardex"
        unique_together = [("alumno", "materia", "intento")]
        ordering = ["alumno", "ciclo_escolar", "materia"]

    def __str__(self) -> str:
        return f"{self.alumno} - {self.materia} ({self.get_estatus_display()})"


class DocumentoAlumno(models.Model):
    """Documento del expediente del alumno (acta, CURP, certificados, etc.)."""

    class TipoDocumento(models.TextChoices):
        ACTA_NACIMIENTO = "ACTA_NACIMIENTO", "Acta de nacimiento"
        CURP = "CURP", "CURP"
        COMPROBANTE_DOMICILIO = "COMPROBANTE_DOMICILIO", "Comprobante de domicilio"
        CERTIFICADO_ESTUDIOS = "CERTIFICADO_ESTUDIOS", "Certificado de estudios previos"
        IDENTIFICACION = "IDENTIFICACION", "Identificación oficial"
        FOTOGRAFIA = "FOTOGRAFIA", "Fotografía"
        OTRO = "OTRO", "Otro"

    alumno = models.ForeignKey(
        Alumno, on_delete=models.CASCADE, related_name="documentos"
    )
    tipo_documento = models.CharField(max_length=25, choices=TipoDocumento.choices)
    archivo = models.FileField(
        upload_to="alumnos/documentos/%Y/%m/",
        validators=[
            FileExtensionValidator(allowed_extensions=EXTENSIONES_DOCUMENTOS_PERMITIDAS),
            validar_tamano_documento,
        ],
        help_text="Formatos permitidos: PDF, JPG, PNG. Máximo 5 MB.",
    )
    fecha_carga = models.DateTimeField(auto_now_add=True)
    verificado = models.BooleanField(default=False)
    observaciones = models.TextField(blank=True)

    class Meta:
        verbose_name = "Documento de alumno"
        verbose_name_plural = "Documentos de alumnos"
        ordering = ["-fecha_carga"]

    def __str__(self) -> str:
        return f"{self.alumno} - {self.get_tipo_documento_display()}"
