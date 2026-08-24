"""Vistas del portal para el rol ADMINISTRATIVO: gestión de incidencias
(CRUD) y su bitácora de seguimiento (lista + agregar).

La bitácora de seguimientos es intencionalmente de solo lectura una vez
creada (no se permite editar/eliminar un seguimiento ya registrado, para
conservar la trazabilidad del caso); el resto de las pantallas sigue el
patrón CRUD completo del proyecto."""
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from apps.core.mixins import AjaxDeleteView, AjaxModalFormMixin, AjaxTemplateMixin, RoleRequiredMixin
from apps.core.models import Usuario
from apps.incidencias.models import Incidencia, SeguimientoIncidencia

from .forms import IncidenciaForm, SeguimientoIncidenciaForm


class IncidenciaListView(RoleRequiredMixin, AjaxTemplateMixin, ListView):
    roles_permitidos = [Usuario.Rol.ADMINISTRATIVO, Usuario.Rol.DIRECTIVO]
    model = Incidencia
    context_object_name = "incidencias"
    template_name = "portal/administrativos/incidencias_list.html"
    template_name_ajax = "portal/administrativos/partials/_incidencias_tabla.html"

    def get_queryset(self):
        return Incidencia.objects.select_related(
            "persona_involucrada", "tipo"
        ).order_by("-fecha")


class IncidenciaCreateView(RoleRequiredMixin, AjaxModalFormMixin, CreateView):
    roles_permitidos = [Usuario.Rol.ADMINISTRATIVO, Usuario.Rol.DIRECTIVO]
    model = Incidencia
    form_class = IncidenciaForm
    template_name_ajax = "portal/administrativos/partials/_incidencia_form.html"
    success_url = reverse_lazy("portal:admin_incidencias_lista")

    def form_valid(self, form):
        form.instance.registrado_por = self.request.user
        return super().form_valid(form)


class IncidenciaUpdateView(RoleRequiredMixin, AjaxModalFormMixin, UpdateView):
    roles_permitidos = [Usuario.Rol.ADMINISTRATIVO, Usuario.Rol.DIRECTIVO]
    model = Incidencia
    form_class = IncidenciaForm
    template_name_ajax = "portal/administrativos/partials/_incidencia_form.html"
    success_url = reverse_lazy("portal:admin_incidencias_lista")


class IncidenciaDeleteView(RoleRequiredMixin, AjaxDeleteView):
    roles_permitidos = [Usuario.Rol.ADMINISTRATIVO, Usuario.Rol.DIRECTIVO]
    model = Incidencia


class SeguimientoListView(RoleRequiredMixin, AjaxTemplateMixin, ListView):
    roles_permitidos = [Usuario.Rol.ADMINISTRATIVO, Usuario.Rol.DIRECTIVO]
    context_object_name = "seguimientos"
    template_name = "portal/administrativos/seguimientos_list.html"
    template_name_ajax = "portal/administrativos/partials/_seguimientos_tabla.html"

    def get_incidencia(self):
        return get_object_or_404(Incidencia, pk=self.kwargs["incidencia_pk"])

    def get_queryset(self):
        self.incidencia = self.get_incidencia()
        return SeguimientoIncidencia.objects.filter(
            incidencia=self.incidencia
        ).select_related("usuario")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["incidencia"] = self.incidencia
        return context


class SeguimientoCreateView(RoleRequiredMixin, AjaxModalFormMixin, CreateView):
    roles_permitidos = [Usuario.Rol.ADMINISTRATIVO, Usuario.Rol.DIRECTIVO]
    model = SeguimientoIncidencia
    form_class = SeguimientoIncidenciaForm
    template_name_ajax = "portal/administrativos/partials/_seguimiento_form.html"

    def get_incidencia(self):
        return get_object_or_404(Incidencia, pk=self.kwargs["incidencia_pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["incidencia"] = self.get_incidencia()
        return context

    def form_valid(self, form):
        form.instance.incidencia = self.get_incidencia()
        form.instance.usuario = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "portal:admin_seguimientos_lista",
            kwargs={"incidencia_pk": self.object.incidencia_id},
        )
