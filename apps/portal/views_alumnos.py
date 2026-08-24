"""Vistas del portal para el rol ALUMNO: listado de tareas de sus materias
inscritas y gestión de sus propias entregas (subir/editar/eliminar archivo).

Mismo patrón CRUD del proyecto: lista + acciones por renglón (aquí:
"Entregar" cuando no hay entrega todavía, o "Editar"/"Eliminar" cuando ya
existe una)."""
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView, UpdateView

from apps.core.mixins import AjaxDeleteView, AjaxModalFormMixin, AjaxTemplateMixin, RoleRequiredMixin
from apps.core.models import Usuario
from apps.inscripciones.models import Inscripcion
from apps.trabajos.models import EntregaTrabajo, Tarea

from .forms import EntregaAlumnoForm


def _alumno_de(request):
    return getattr(request.user, "perfil_alumno", None)


class AlumnoTareaListView(RoleRequiredMixin, AjaxTemplateMixin, TemplateView):
    """Tareas de los grupos en los que el alumno está inscrito, junto con el
    estado de su propia entrega (si existe)."""

    roles_permitidos = [Usuario.Rol.ALUMNO]
    template_name = "portal/alumnos/tareas_list.html"
    template_name_ajax = "portal/alumnos/partials/_tareas_tabla.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        alumno = _alumno_de(self.request)
        context["alumno"] = alumno
        if alumno is None:
            context["filas"] = []
            return context

        inscripcion = (
            Inscripcion.objects.filter(alumno=alumno)
            .order_by("-ciclo_escolar__fecha_inicio")
            .first()
        )
        grupo_ids = []
        if inscripcion is not None:
            grupo_ids = list(inscripcion.materias.values_list("grupo_id", flat=True))

        tareas = Tarea.objects.filter(grupo_id__in=grupo_ids).select_related(
            "grupo__materia"
        )
        entregas_por_tarea = {
            e.tarea_id: e
            for e in EntregaTrabajo.objects.filter(alumno=alumno, tarea__in=tareas)
        }
        context["filas"] = [
            {"tarea": tarea, "entrega": entregas_por_tarea.get(tarea.id)}
            for tarea in tareas.order_by("fecha_entrega")
        ]
        return context


class EntregaCreateView(RoleRequiredMixin, AjaxModalFormMixin, CreateView):
    roles_permitidos = [Usuario.Rol.ALUMNO]
    model = EntregaTrabajo
    form_class = EntregaAlumnoForm
    template_name_ajax = "portal/alumnos/partials/_entrega_form.html"
    success_url = reverse_lazy("portal:alumno_tareas_lista")

    def get_tarea(self):
        return get_object_or_404(Tarea, pk=self.kwargs["tarea_pk"], activa=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tarea"] = self.get_tarea()
        return context

    def form_valid(self, form):
        form.instance.tarea = self.get_tarea()
        form.instance.alumno = _alumno_de(self.request)
        return super().form_valid(form)


class EntregaUpdateView(RoleRequiredMixin, AjaxModalFormMixin, UpdateView):
    roles_permitidos = [Usuario.Rol.ALUMNO]
    model = EntregaTrabajo
    form_class = EntregaAlumnoForm
    template_name_ajax = "portal/alumnos/partials/_entrega_form.html"
    success_url = reverse_lazy("portal:alumno_tareas_lista")

    def get_queryset(self):
        return EntregaTrabajo.objects.filter(alumno=_alumno_de(self.request))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tarea"] = self.object.tarea
        return context


class EntregaDeleteView(RoleRequiredMixin, AjaxDeleteView):
    roles_permitidos = [Usuario.Rol.ALUMNO]
    model = EntregaTrabajo

    def get_queryset(self):
        return EntregaTrabajo.objects.filter(alumno=_alumno_de(self.request))
