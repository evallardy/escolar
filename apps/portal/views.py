from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView

from apps.core.mixins import AjaxTemplateMixin, RoleRequiredMixin
from apps.core.models import Usuario


class DashboardRouterView(LoginRequiredMixin, View):
    """Redirige al dashboard correspondiente según el rol del usuario autenticado."""

    def get(self, request, *args, **kwargs):
        return redirect(reverse(request.user.dashboard_url_name()))


class DashboardGenericoView(LoginRequiredMixin, AjaxTemplateMixin, TemplateView):
    """Pantalla de respaldo para usuarios sin rol asignado (o superuser puro)."""

    template_name = "portal/dashboard_generico.html"
    template_name_ajax = "portal/partials/dashboard_generico_partial.html"


class DashboardPadresView(RoleRequiredMixin, AjaxTemplateMixin, TemplateView):
    roles_permitidos = [Usuario.Rol.PADRE]
    template_name = "portal/dashboard_padres.html"
    template_name_ajax = "portal/partials/dashboard_padres_partial.html"


class DashboardAlumnosView(RoleRequiredMixin, AjaxTemplateMixin, TemplateView):
    roles_permitidos = [Usuario.Rol.ALUMNO]
    template_name = "portal/dashboard_alumnos.html"
    template_name_ajax = "portal/partials/dashboard_alumnos_partial.html"


class DashboardDocentesView(RoleRequiredMixin, AjaxTemplateMixin, TemplateView):
    roles_permitidos = [Usuario.Rol.DOCENTE]
    template_name = "portal/dashboard_docentes.html"
    template_name_ajax = "portal/partials/dashboard_docentes_partial.html"


class DashboardAdministrativosView(RoleRequiredMixin, AjaxTemplateMixin, TemplateView):
    roles_permitidos = [Usuario.Rol.ADMINISTRATIVO]
    template_name = "portal/dashboard_administrativos.html"
    template_name_ajax = "portal/partials/dashboard_administrativos_partial.html"


class DashboardDirectivosView(RoleRequiredMixin, AjaxTemplateMixin, TemplateView):
    roles_permitidos = [Usuario.Rol.DIRECTIVO]
    template_name = "portal/dashboard_directivos.html"
    template_name_ajax = "portal/partials/dashboard_directivos_partial.html"
