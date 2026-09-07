"""Registro central del Panel Ejecutivo.

Replica, para presentación, la misma información que cada modelo expone en
``django.contrib.admin`` (list_display/list_filter/search_fields), pero con
una interfaz propia de diseño ejecutivo. Cada entrada de ``REGISTRO`` es
autosuficiente: las vistas y templates genéricos de ``apps/panel`` recorren
este diccionario para construir listados, filtros, búsqueda y formularios
sin necesitar una vista/plantilla distinta por modelo.
"""
from dataclasses import dataclass

from apps.academico.models import (
    CalendarioEvento,
    CicloEscolar,
    Grupo,
    Materia,
    NivelEducativo,
    PlanEstudios,
    Programa,
)
from apps.alumnos.models import Alumno, Cardex, DocumentoAlumno, Tutor
from apps.asistencia.models import (
    DispositivoBiometrico,
    ParametroGPS,
    RegistroAsistencia,
    UbicacionGPS,
)
from apps.core.models import Plantel, Usuario
from apps.docentes.models import AsignacionDocente, Docente
from apps.finanzas.models import Beca, CargoAlumno, ConceptoCobro, Pago
from apps.incidencias.models import Incidencia, TipoIncidencia
from apps.inscripciones.models import Inscripcion, InscripcionMateria
from apps.nomina.models import Empleado, PeriodoNomina, Puesto, ReciboNomina
from apps.trabajos.models import EntregaTrabajo, Tarea


@dataclass
class PanelModelConfig:
    model: type
    modulo: str
    verbose_name: str
    verbose_name_plural: str
    list_display: tuple = ()
    list_filter: tuple = ()
    search_fields: tuple = ()
    ordering: tuple | None = None
    select_related: tuple = ()
    form_exclude: tuple = ()
    tiene_archivos: bool = False
    icono: str = "bi-table"

    @property
    def clave(self) -> str:
        return self.model._meta.label_lower  # p. ej. "academico.programa"

    @property
    def app_label(self) -> str:
        return self.model._meta.app_label

    @property
    def model_name(self) -> str:
        return self.model._meta.model_name


MODULOS = [
    {"clave": "core", "nombre": "Institución y usuarios", "icono": "bi-building", "color": "#1f4e79"},
    {"clave": "academico", "nombre": "Académico", "icono": "bi-mortarboard", "color": "#0e7c86"},
    {"clave": "alumnos", "nombre": "Alumnos", "icono": "bi-people", "color": "#2f7fc1"},
    {"clave": "docentes", "nombre": "Docentes", "icono": "bi-person-workspace", "color": "#6a4c93"},
    {"clave": "inscripciones", "nombre": "Inscripciones", "icono": "bi-journal-check", "color": "#1f8a70"},
    {"clave": "finanzas", "nombre": "Finanzas", "icono": "bi-cash-coin", "color": "#b8860b"},
    {"clave": "asistencia", "nombre": "Asistencia y GPS", "icono": "bi-fingerprint", "color": "#c0392b"},
    {"clave": "nomina", "nombre": "Nómina", "icono": "bi-wallet2", "color": "#2e6e9e"},
    {"clave": "incidencias", "nombre": "Incidencias", "icono": "bi-exclamation-triangle", "color": "#d35400"},
    {"clave": "trabajos", "nombre": "Trabajos y tareas", "icono": "bi-journal-text", "color": "#4a5a6a"},
]

# Campos que jamás deben exponerse en un formulario genérico (contraseñas,
# permisos de sistema): se gestionan exclusivamente desde el admin de Django.
_USUARIO_EXCLUYE = ("password", "last_login", "is_superuser", "groups", "user_permissions")

_CONFIGS: list[PanelModelConfig] = [
    # ---------------------------------------------------------------- core
    PanelModelConfig(
        model=Plantel,
        modulo="core",
        verbose_name="Plantel",
        verbose_name_plural="Planteles",
        list_display=("clave", "nombre", "activo"),
        list_filter=("activo",),
        search_fields=("clave", "nombre"),
        tiene_archivos=True,
        icono="bi-building",
    ),
    PanelModelConfig(
        model=Usuario,
        modulo="core",
        verbose_name="Usuario",
        verbose_name_plural="Usuarios",
        list_display=("username", "get_full_name", "rol_principal", "is_active", "is_staff"),
        list_filter=("is_active", "is_staff", "rol_principal"),
        search_fields=("username", "first_name", "last_name", "email"),
        form_exclude=_USUARIO_EXCLUYE,
        tiene_archivos=True,
        icono="bi-person-badge",
    ),
    # ----------------------------------------------------------- académico
    PanelModelConfig(
        model=NivelEducativo,
        modulo="academico",
        verbose_name="Nivel educativo",
        verbose_name_plural="Niveles educativos",
        list_display=("clave", "nombre", "orden", "activo", "esta_vigente"),
        list_filter=("activo",),
        search_fields=("clave", "nombre"),
        ordering=("orden",),
        icono="bi-signpost-split",
    ),
    PanelModelConfig(
        model=Programa,
        modulo="academico",
        verbose_name="Programa",
        verbose_name_plural="Programas",
        list_display=("clave", "nombre", "nivel", "plantel", "modalidad", "activo"),
        list_filter=("nivel", "plantel", "modalidad", "activo"),
        search_fields=("clave", "nombre"),
        select_related=("nivel", "plantel"),
        icono="bi-diagram-3",
    ),
    PanelModelConfig(
        model=PlanEstudios,
        modulo="academico",
        verbose_name="Plan de estudios",
        verbose_name_plural="Planes de estudios",
        list_display=("programa", "version", "total_creditos", "activo"),
        list_filter=("programa__nivel", "activo"),
        search_fields=("programa__nombre", "version"),
        select_related=("programa",),
        icono="bi-journal-bookmark",
    ),
    PanelModelConfig(
        model=Materia,
        modulo="academico",
        verbose_name="Materia",
        verbose_name_plural="Materias",
        list_display=("clave", "nombre", "plan_estudios", "periodo", "creditos", "tipo", "activo"),
        list_filter=("plan_estudios__programa", "tipo", "activo"),
        search_fields=("clave", "nombre"),
        select_related=("plan_estudios",),
        icono="bi-book",
    ),
    PanelModelConfig(
        model=CicloEscolar,
        modulo="academico",
        verbose_name="Ciclo escolar",
        verbose_name_plural="Ciclos escolares",
        list_display=("clave", "nombre", "plantel", "fecha_inicio", "fecha_fin", "activo"),
        list_filter=("plantel", "activo"),
        search_fields=("clave", "nombre"),
        select_related=("plantel",),
        icono="bi-calendar3",
    ),
    PanelModelConfig(
        model=CalendarioEvento,
        modulo="academico",
        verbose_name="Evento de calendario",
        verbose_name_plural="Eventos de calendario",
        list_display=("nombre", "ciclo_escolar", "tipo", "fecha_inicio", "fecha_fin"),
        list_filter=("tipo", "ciclo_escolar"),
        search_fields=("nombre",),
        select_related=("ciclo_escolar",),
        icono="bi-calendar-event",
    ),
    PanelModelConfig(
        model=Grupo,
        modulo="academico",
        verbose_name="Grupo",
        verbose_name_plural="Grupos",
        list_display=("__str__", "materia", "aula", "ciclo_escolar", "turno", "cupo_maximo", "activo"),
        list_filter=("ciclo_escolar", "turno", "activo"),
        search_fields=("clave", "materia__nombre", "materia__clave"),
        select_related=("materia", "ciclo_escolar"),
        icono="bi-people-fill",
    ),
    # ------------------------------------------------------------ alumnos
    PanelModelConfig(
        model=Alumno,
        modulo="alumnos",
        verbose_name="Alumno",
        verbose_name_plural="Alumnos",
        list_display=("matricula", "__str__", "programa", "plantel", "estatus"),
        list_filter=("programa", "plantel", "estatus"),
        search_fields=("matricula", "usuario__first_name", "usuario__last_name", "usuario__username", "curp"),
        select_related=("usuario", "programa", "plantel"),
        icono="bi-person-vcard",
    ),
    PanelModelConfig(
        model=Tutor,
        modulo="alumnos",
        verbose_name="Tutor",
        verbose_name_plural="Tutores",
        list_display=("__str__", "telefono", "ocupacion"),
        search_fields=("usuario__first_name", "usuario__last_name", "usuario__username"),
        select_related=("usuario",),
        icono="bi-person-hearts",
    ),
    PanelModelConfig(
        model=Cardex,
        modulo="alumnos",
        verbose_name="Registro de cardex",
        verbose_name_plural="Cardex",
        list_display=("alumno", "materia", "ciclo_escolar", "calificacion", "estatus"),
        list_filter=("estatus", "ciclo_escolar"),
        search_fields=("alumno__matricula", "materia__nombre", "materia__clave"),
        select_related=("alumno", "materia", "ciclo_escolar"),
        icono="bi-card-checklist",
    ),
    PanelModelConfig(
        model=DocumentoAlumno,
        modulo="alumnos",
        verbose_name="Documento de alumno",
        verbose_name_plural="Documentos de alumnos",
        list_display=("alumno", "tipo_documento", "fecha_carga", "verificado"),
        list_filter=("tipo_documento", "verificado"),
        search_fields=("alumno__matricula",),
        select_related=("alumno",),
        tiene_archivos=True,
        icono="bi-file-earmark-text",
    ),
    # ----------------------------------------------------------- docentes
    PanelModelConfig(
        model=Docente,
        modulo="docentes",
        verbose_name="Docente",
        verbose_name_plural="Docentes",
        list_display=("__str__", "numero_empleado", "especialidad", "nivel_estudios", "activo"),
        list_filter=("nivel_estudios", "activo", "planteles"),
        search_fields=("numero_empleado", "usuario__first_name", "usuario__last_name", "usuario__username", "rfc", "curp"),
        select_related=("usuario",),
        icono="bi-person-workspace",
    ),
    PanelModelConfig(
        model=AsignacionDocente,
        modulo="docentes",
        verbose_name="Asignación docente",
        verbose_name_plural="Asignaciones docentes",
        list_display=("docente", "grupo", "fecha_inicio", "fecha_fin", "activo"),
        list_filter=("activo",),
        search_fields=("docente__usuario__first_name", "docente__usuario__last_name", "grupo__clave"),
        select_related=("docente", "grupo"),
        icono="bi-clipboard-check",
    ),
    # ------------------------------------------------------- inscripciones
    PanelModelConfig(
        model=Inscripcion,
        modulo="inscripciones",
        verbose_name="Inscripción",
        verbose_name_plural="Inscripciones",
        list_display=("alumno", "programa", "ciclo_escolar", "estatus", "fecha_inscripcion"),
        list_filter=("ciclo_escolar", "programa", "estatus"),
        search_fields=("alumno__matricula", "alumno__usuario__first_name", "alumno__usuario__last_name"),
        select_related=("alumno", "programa", "ciclo_escolar"),
        icono="bi-journal-check",
    ),
    PanelModelConfig(
        model=InscripcionMateria,
        modulo="inscripciones",
        verbose_name="Inscripción a materia",
        verbose_name_plural="Inscripciones a materias",
        list_display=("inscripcion", "grupo", "estatus", "calificacion_final"),
        list_filter=("estatus",),
        search_fields=("inscripcion__alumno__matricula", "grupo__clave"),
        select_related=("inscripcion", "grupo"),
        icono="bi-list-check",
    ),
    # ----------------------------------------------------------- finanzas
    PanelModelConfig(
        model=ConceptoCobro,
        modulo="finanzas",
        verbose_name="Concepto de cobro",
        verbose_name_plural="Conceptos de cobro",
        list_display=("nombre", "plantel", "programa", "periodicidad", "monto", "activo", "esta_vigente"),
        list_filter=("plantel", "periodicidad", "activo"),
        search_fields=("nombre",),
        select_related=("plantel", "programa"),
        icono="bi-tag",
    ),
    PanelModelConfig(
        model=CargoAlumno,
        modulo="finanzas",
        verbose_name="Cargo de alumno",
        verbose_name_plural="Cargos de alumnos",
        list_display=("alumno", "concepto", "ciclo_escolar", "monto", "saldo_pendiente", "fecha_limite", "estatus"),
        list_filter=("estatus", "ciclo_escolar", "concepto"),
        search_fields=("alumno__matricula", "concepto__nombre"),
        select_related=("alumno", "concepto", "ciclo_escolar"),
        icono="bi-receipt",
    ),
    PanelModelConfig(
        model=Pago,
        modulo="finanzas",
        verbose_name="Pago",
        verbose_name_plural="Pagos",
        list_display=("cargo", "monto", "fecha_pago", "forma_pago", "origen"),
        list_filter=("forma_pago", "origen"),
        search_fields=("cargo__alumno__matricula", "referencia_transaccion"),
        select_related=("cargo",),
        icono="bi-cash-stack",
    ),
    PanelModelConfig(
        model=Beca,
        modulo="finanzas",
        verbose_name="Beca",
        verbose_name_plural="Becas",
        list_display=("alumno", "concepto", "tipo", "valor", "activo"),
        list_filter=("tipo", "activo"),
        search_fields=("alumno__matricula", "motivo"),
        select_related=("alumno", "concepto"),
        icono="bi-award",
    ),
    # --------------------------------------------------------- asistencia
    PanelModelConfig(
        model=DispositivoBiometrico,
        modulo="asistencia",
        verbose_name="Dispositivo biométrico",
        verbose_name_plural="Dispositivos biométricos",
        list_display=("identificador", "marca", "modelo", "plantel", "ubicacion", "activo"),
        list_filter=("plantel", "activo"),
        search_fields=("identificador", "marca", "modelo"),
        select_related=("plantel",),
        form_exclude=("clave_api",),
        icono="bi-fingerprint",
    ),
    PanelModelConfig(
        model=RegistroAsistencia,
        modulo="asistencia",
        verbose_name="Registro de asistencia",
        verbose_name_plural="Registros de asistencia",
        list_display=("persona", "tipo", "origen", "fecha_hora", "dispositivo"),
        list_filter=("tipo", "origen", "dispositivo"),
        search_fields=("persona__username", "persona__first_name", "persona__last_name"),
        select_related=("persona", "dispositivo"),
        icono="bi-clock-history",
    ),
    PanelModelConfig(
        model=ParametroGPS,
        modulo="asistencia",
        verbose_name="Parámetro GPS",
        verbose_name_plural="Parámetros GPS",
        list_display=("plantel", "intervalo_minutos", "activo"),
        select_related=("plantel",),
        icono="bi-geo-alt",
    ),
    PanelModelConfig(
        model=UbicacionGPS,
        modulo="asistencia",
        verbose_name="Ubicación GPS",
        verbose_name_plural="Ubicaciones GPS",
        list_display=("persona", "latitud", "longitud", "dentro_del_plantel", "timestamp"),
        list_filter=("dentro_del_plantel",),
        search_fields=("persona__username", "persona__first_name", "persona__last_name"),
        select_related=("persona",),
        icono="bi-geo",
    ),
    # ------------------------------------------------------------- nómina
    PanelModelConfig(
        model=Puesto,
        modulo="nomina",
        verbose_name="Puesto",
        verbose_name_plural="Puestos",
        list_display=("nombre", "plantel", "sueldo_base"),
        list_filter=("plantel",),
        search_fields=("nombre",),
        select_related=("plantel",),
        icono="bi-briefcase",
    ),
    PanelModelConfig(
        model=Empleado,
        modulo="nomina",
        verbose_name="Empleado",
        verbose_name_plural="Empleados",
        list_display=("__str__", "puesto", "rfc", "activo"),
        list_filter=("puesto", "activo"),
        search_fields=("usuario__first_name", "usuario__last_name", "usuario__username", "rfc"),
        select_related=("usuario", "puesto"),
        icono="bi-person-badge",
    ),
    PanelModelConfig(
        model=PeriodoNomina,
        modulo="nomina",
        verbose_name="Periodo de nómina",
        verbose_name_plural="Periodos de nómina",
        list_display=("__str__", "tipo", "fecha_inicio", "fecha_fin", "cerrado"),
        list_filter=("tipo", "cerrado"),
        search_fields=(),
        icono="bi-calendar-range",
    ),
    PanelModelConfig(
        model=ReciboNomina,
        modulo="nomina",
        verbose_name="Recibo de nómina",
        verbose_name_plural="Recibos de nómina",
        list_display=("empleado", "periodo", "percepciones", "deducciones", "neto", "estatus_timbrado"),
        list_filter=("estatus_timbrado", "periodo"),
        search_fields=("empleado__usuario__first_name", "empleado__usuario__last_name", "uuid_cfdi"),
        select_related=("empleado", "periodo"),
        form_exclude=("neto",),
        tiene_archivos=True,
        icono="bi-file-earmark-spreadsheet",
    ),
    # -------------------------------------------------------- incidencias
    PanelModelConfig(
        model=TipoIncidencia,
        modulo="incidencias",
        verbose_name="Tipo de incidencia",
        verbose_name_plural="Tipos de incidencia",
        list_display=("clave", "nombre", "gravedad", "activo"),
        list_filter=("gravedad", "activo"),
        search_fields=("clave", "nombre"),
        icono="bi-tags",
    ),
    PanelModelConfig(
        model=Incidencia,
        modulo="incidencias",
        verbose_name="Incidencia",
        verbose_name_plural="Incidencias",
        list_display=("persona_involucrada", "tipo", "fecha", "estatus", "registrado_por"),
        list_filter=("estatus", "tipo"),
        search_fields=("persona_involucrada__first_name", "persona_involucrada__last_name", "persona_involucrada__username"),
        select_related=("persona_involucrada", "tipo", "registrado_por"),
        tiene_archivos=True,
        icono="bi-exclamation-triangle",
    ),
    # ---------------------------------------------------------- trabajos
    PanelModelConfig(
        model=Tarea,
        modulo="trabajos",
        verbose_name="Tarea",
        verbose_name_plural="Tareas",
        list_display=("titulo", "grupo", "docente", "fecha_entrega", "activa"),
        list_filter=("activa", "grupo"),
        search_fields=("titulo", "grupo__clave"),
        select_related=("grupo", "docente"),
        icono="bi-journal-text",
    ),
    PanelModelConfig(
        model=EntregaTrabajo,
        modulo="trabajos",
        verbose_name="Entrega de trabajo",
        verbose_name_plural="Entregas de trabajos",
        list_display=("alumno", "tarea", "fecha_entrega", "calificacion", "entregado_tarde"),
        list_filter=("tarea__grupo",),
        search_fields=("alumno__matricula", "tarea__titulo"),
        select_related=("alumno", "tarea"),
        tiene_archivos=True,
        icono="bi-upload",
    ),
]

REGISTRO: dict[str, PanelModelConfig] = {cfg.clave: cfg for cfg in _CONFIGS}


def obtener_config(app_label: str, model_name: str) -> PanelModelConfig:
    clave = f"{app_label}.{model_name}".lower()
    if clave not in REGISTRO:
        from django.http import Http404

        raise Http404(f"'{clave}' no está registrado en el Panel Ejecutivo.")
    return REGISTRO[clave]


def configs_por_modulo() -> dict:
    resultado = {m["clave"]: {**m, "modelos": []} for m in MODULOS}
    for cfg in _CONFIGS:
        resultado[cfg.modulo]["modelos"].append(cfg)
    return resultado
