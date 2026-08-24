"""Vistas del portal para el rol ADMINISTRATIVO: conceptos de cobro, cargos
de alumnos y los pagos aplicados a cada cargo. Mismo patrón CRUD del
proyecto en las tres pantallas."""
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from apps.core.mixins import AjaxDeleteView, AjaxModalFormMixin, AjaxTemplateMixin, RoleRequiredMixin
from apps.core.models import Usuario
from apps.finanzas.models import CargoAlumno, ConceptoCobro, Pago

from .forms import CargoAlumnoForm, ConceptoCobroForm, PagoForm

ROLES_FINANZAS = [Usuario.Rol.ADMINISTRATIVO, Usuario.Rol.DIRECTIVO]


# --------------------------------------------------------------------------
# Conceptos de cobro
# --------------------------------------------------------------------------


class ConceptoCobroListView(RoleRequiredMixin, AjaxTemplateMixin, ListView):
    roles_permitidos = ROLES_FINANZAS
    model = ConceptoCobro
    context_object_name = "conceptos"
    template_name = "portal/administrativos/conceptos_list.html"
    template_name_ajax = "portal/administrativos/partials/_conceptos_tabla.html"

    def get_queryset(self):
        return ConceptoCobro.objects.select_related("plantel", "programa").order_by(
            "plantel", "nombre"
        )


class ConceptoCobroCreateView(RoleRequiredMixin, AjaxModalFormMixin, CreateView):
    roles_permitidos = ROLES_FINANZAS
    model = ConceptoCobro
    form_class = ConceptoCobroForm
    template_name_ajax = "portal/administrativos/partials/_concepto_form.html"
    success_url = reverse_lazy("portal:admin_conceptos_lista")


class ConceptoCobroUpdateView(RoleRequiredMixin, AjaxModalFormMixin, UpdateView):
    roles_permitidos = ROLES_FINANZAS
    model = ConceptoCobro
    form_class = ConceptoCobroForm
    template_name_ajax = "portal/administrativos/partials/_concepto_form.html"
    success_url = reverse_lazy("portal:admin_conceptos_lista")


class ConceptoCobroDeleteView(RoleRequiredMixin, AjaxDeleteView):
    roles_permitidos = ROLES_FINANZAS
    model = ConceptoCobro


# --------------------------------------------------------------------------
# Cargos de alumnos
# --------------------------------------------------------------------------


class CargoAlumnoListView(RoleRequiredMixin, AjaxTemplateMixin, ListView):
    roles_permitidos = ROLES_FINANZAS
    model = CargoAlumno
    context_object_name = "cargos"
    template_name = "portal/administrativos/cargos_list.html"
    template_name_ajax = "portal/administrativos/partials/_cargos_tabla.html"

    def get_queryset(self):
        return CargoAlumno.objects.select_related(
            "alumno__usuario", "concepto", "ciclo_escolar"
        ).order_by("-fecha_limite")


class CargoAlumnoCreateView(RoleRequiredMixin, AjaxModalFormMixin, CreateView):
    roles_permitidos = ROLES_FINANZAS
    model = CargoAlumno
    form_class = CargoAlumnoForm
    template_name_ajax = "portal/administrativos/partials/_cargo_form.html"
    success_url = reverse_lazy("portal:admin_cargos_lista")


class CargoAlumnoUpdateView(RoleRequiredMixin, AjaxModalFormMixin, UpdateView):
    roles_permitidos = ROLES_FINANZAS
    model = CargoAlumno
    form_class = CargoAlumnoForm
    template_name_ajax = "portal/administrativos/partials/_cargo_form.html"
    success_url = reverse_lazy("portal:admin_cargos_lista")


class CargoAlumnoDeleteView(RoleRequiredMixin, AjaxDeleteView):
    roles_permitidos = ROLES_FINANZAS
    model = CargoAlumno


# --------------------------------------------------------------------------
# Pagos (siempre en el contexto de un cargo específico)
# --------------------------------------------------------------------------


class PagoListView(RoleRequiredMixin, AjaxTemplateMixin, ListView):
    roles_permitidos = ROLES_FINANZAS
    context_object_name = "pagos"
    template_name = "portal/administrativos/pagos_list.html"
    template_name_ajax = "portal/administrativos/partials/_pagos_tabla.html"

    def get_cargo(self):
        return get_object_or_404(CargoAlumno, pk=self.kwargs["cargo_pk"])

    def get_queryset(self):
        self.cargo = self.get_cargo()
        return Pago.objects.filter(cargo=self.cargo).order_by("-fecha_pago")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cargo"] = self.cargo
        return context


class PagoCreateView(RoleRequiredMixin, AjaxModalFormMixin, CreateView):
    roles_permitidos = ROLES_FINANZAS
    model = Pago
    form_class = PagoForm
    template_name_ajax = "portal/administrativos/partials/_pago_form.html"

    def get_cargo(self):
        return get_object_or_404(CargoAlumno, pk=self.kwargs["cargo_pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cargo"] = self.get_cargo()
        return context

    def form_valid(self, form):
        form.instance.cargo = self.get_cargo()
        form.instance.capturado_por = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("portal:admin_pagos_lista", kwargs={"cargo_pk": self.object.cargo_id})


class PagoUpdateView(RoleRequiredMixin, AjaxModalFormMixin, UpdateView):
    roles_permitidos = ROLES_FINANZAS
    model = Pago
    form_class = PagoForm
    template_name_ajax = "portal/administrativos/partials/_pago_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cargo"] = self.object.cargo
        return context

    def get_success_url(self):
        return reverse_lazy("portal:admin_pagos_lista", kwargs={"cargo_pk": self.object.cargo_id})


class PagoDeleteView(RoleRequiredMixin, AjaxDeleteView):
    roles_permitidos = ROLES_FINANZAS
    model = Pago
