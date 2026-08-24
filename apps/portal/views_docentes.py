"""Vistas del portal para el rol DOCENTE: gestión de tareas (CRUD) y
calificación de entregas de sus alumnos.

Todas siguen el mismo patrón CRUD del proyecto: lista con botón "Agregar" y
acciones "Editar"/"Eliminar" por renglón, con formularios en modal AJAX.
"""
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from apps.core.mixins import AjaxDeleteView, AjaxModalFormMixin, AjaxTemplateMixin, RoleRequiredMixin
from apps.core.models import Usuario
from apps.trabajos.models import EntregaTrabajo, Tarea

from .forms import EntregaCalificarForm, TareaForm


class DocenteTareaQuerysetMixin:
    """Limita cualquier vista a las tareas del docente autenticado (control
    de acceso en el backend, nunca solo ocultando botones en el frontend)."""

    def get_docente(self):
        return getattr(self.request.user, "perfil_docente", None)

    def get_queryset(self):
        docente = self.get_docente()
        if docente is None:
            return Tarea.objects.none()
        return Tarea.objects.filter(docente=docente).select_related(
            "grupo__materia", "grupo__ciclo_escolar"
        )


class TareaListView(RoleRequiredMixin, DocenteTareaQuerysetMixin, AjaxTemplateMixin, ListView):
    roles_permitidos = [Usuario.Rol.DOCENTE]
    context_object_name = "tareas"
    template_name = "portal/docentes/tareas_list.html"
    template_name_ajax = "portal/docentes/partials/_tareas_tabla.html"


class TareaCreateView(RoleRequiredMixin, DocenteTareaQuerysetMixin, AjaxModalFormMixin, CreateView):
    roles_permitidos = [Usuario.Rol.DOCENTE]
    model = Tarea
    form_class = TareaForm
    template_name_ajax = "portal/docentes/partials/_tarea_form.html"
    success_url = reverse_lazy("portal:docente_tareas_lista")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["docente"] = self.get_docente()
        return kwargs

    def form_valid(self, form):
        form.instance.docente = self.get_docente()
        return super().form_valid(form)


class TareaUpdateView(RoleRequiredMixin, DocenteTareaQuerysetMixin, AjaxModalFormMixin, UpdateView):
    roles_permitidos = [Usuario.Rol.DOCENTE]
    model = Tarea
    form_class = TareaForm
    template_name_ajax = "portal/docentes/partials/_tarea_form.html"
    success_url = reverse_lazy("portal:docente_tareas_lista")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["docente"] = self.get_docente()
        return kwargs


class TareaDeleteView(RoleRequiredMixin, DocenteTareaQuerysetMixin, AjaxDeleteView):
    roles_permitidos = [Usuario.Rol.DOCENTE]
    model = Tarea


class EntregaListView(RoleRequiredMixin, AjaxTemplateMixin, ListView):
    """Entregas de los alumnos para una tarea del docente autenticado."""

    roles_permitidos = [Usuario.Rol.DOCENTE]
    context_object_name = "entregas"
    template_name = "portal/docentes/entregas_list.html"
    template_name_ajax = "portal/docentes/partials/_entregas_tabla.html"

    def get_tarea(self):
        docente = getattr(self.request.user, "perfil_docente", None)
        return get_object_or_404(Tarea, pk=self.kwargs["tarea_pk"], docente=docente)

    def get_queryset(self):
        self.tarea = self.get_tarea()
        return EntregaTrabajo.objects.filter(tarea=self.tarea).select_related(
            "alumno__usuario"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tarea"] = self.tarea
        return context


class EntregaCalificarView(RoleRequiredMixin, AjaxModalFormMixin, UpdateView):
    roles_permitidos = [Usuario.Rol.DOCENTE]
    model = EntregaTrabajo
    form_class = EntregaCalificarForm
    template_name_ajax = "portal/docentes/partials/_entrega_calificar_form.html"

    def get_queryset(self):
        docente = getattr(self.request.user, "perfil_docente", None)
        return EntregaTrabajo.objects.filter(tarea__docente=docente)

    def get_success_url(self):
        return reverse_lazy(
            "portal:docente_entregas_lista", kwargs={"tarea_pk": self.object.tarea_id}
        )
