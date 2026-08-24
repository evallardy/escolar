"""Formularios usados por las pantallas CRUD del portal (patrón: modal de
alta/edición + lista con acciones por renglón), organizados por módulo."""
from django import forms

from apps.docentes.models import Docente
from apps.finanzas.models import CargoAlumno, ConceptoCobro, Pago
from apps.incidencias.models import Incidencia, SeguimientoIncidencia
from apps.trabajos.models import EntregaTrabajo, Tarea

# --------------------------------------------------------------------------
# Docentes: Tareas y calificación de entregas
# --------------------------------------------------------------------------


class TareaForm(forms.ModelForm):
    """El campo `grupo` se limita, en la vista, a los grupos asignados al
    docente autenticado (ver `TareaForm(docente=...)`)."""

    class Meta:
        model = Tarea
        fields = ["grupo", "titulo", "instrucciones", "fecha_entrega", "activa"]
        widgets = {
            "fecha_entrega": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
            "instrucciones": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, docente: Docente | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fecha_entrega"].input_formats = ["%Y-%m-%dT%H:%M"]
        if docente is not None:
            grupo_ids = docente.asignaciones.filter(activo=True).values_list(
                "grupo_id", flat=True
            )
            self.fields["grupo"].queryset = self.fields["grupo"].queryset.filter(
                id__in=grupo_ids
            )


class EntregaCalificarForm(forms.ModelForm):
    class Meta:
        model = EntregaTrabajo
        fields = ["calificacion", "comentarios"]
        widgets = {"comentarios": forms.Textarea(attrs={"rows": 3})}


# --------------------------------------------------------------------------
# Alumnos: entrega de trabajos
# --------------------------------------------------------------------------


class EntregaAlumnoForm(forms.ModelForm):
    class Meta:
        model = EntregaTrabajo
        fields = ["archivo"]


# --------------------------------------------------------------------------
# Administrativos: incidencias
# --------------------------------------------------------------------------


class IncidenciaForm(forms.ModelForm):
    class Meta:
        model = Incidencia
        fields = [
            "persona_involucrada",
            "tipo",
            "descripcion",
            "fecha",
            "estatus",
            "adjunto",
        ]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 3}),
            "fecha": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fecha"].input_formats = ["%Y-%m-%dT%H:%M"]


class SeguimientoIncidenciaForm(forms.ModelForm):
    class Meta:
        model = SeguimientoIncidencia
        fields = ["comentario"]
        widgets = {"comentario": forms.Textarea(attrs={"rows": 2})}


# --------------------------------------------------------------------------
# Administrativos: finanzas (conceptos de cobro, cargos y pagos)
# --------------------------------------------------------------------------


class ConceptoCobroForm(forms.ModelForm):
    class Meta:
        model = ConceptoCobro
        fields = [
            "plantel",
            "programa",
            "nombre",
            "periodicidad",
            "monto",
            "vigente_desde",
            "vigente_hasta",
            "activo",
        ]
        widgets = {
            "vigente_desde": forms.DateInput(attrs={"type": "date"}),
            "vigente_hasta": forms.DateInput(attrs={"type": "date"}),
        }


class CargoAlumnoForm(forms.ModelForm):
    class Meta:
        model = CargoAlumno
        fields = [
            "alumno",
            "concepto",
            "ciclo_escolar",
            "periodo_etiqueta",
            "monto",
            "fecha_limite",
            "estatus",
        ]
        widgets = {"fecha_limite": forms.DateInput(attrs={"type": "date"})}


class PagoForm(forms.ModelForm):
    class Meta:
        model = Pago
        fields = ["monto", "fecha_pago", "forma_pago", "referencia_transaccion"]
        widgets = {"fecha_pago": forms.DateInput(attrs={"type": "date"})}
