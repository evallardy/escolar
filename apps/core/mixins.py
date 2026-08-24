"""Mixins reutilizables por todas las vistas CBV del proyecto:

- ``AjaxTemplateMixin``: permite que una misma vista responda la página
  completa (extiende base.html) o solo el fragmento parcial cuando la
  petición viene por AJAX (fetch), evitando duplicar lógica de contexto.
- ``RoleRequiredMixin``: protege una vista a un conjunto de roles.
"""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied


AJAX_HEADER = "X-Requested-With"
AJAX_VALUE = "XMLHttpRequest"


class AjaxTemplateMixin:
    """Usa ``template_name_ajax`` (solo el fragmento) cuando la petición es AJAX."""

    template_name_ajax = None

    def is_ajax(self) -> bool:
        return self.request.headers.get(AJAX_HEADER) == AJAX_VALUE

    def get_template_names(self):
        if self.is_ajax() and self.template_name_ajax:
            return [self.template_name_ajax]
        return super().get_template_names()


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Restringe el acceso a la vista a los roles indicados en ``roles_permitidos``.

    Uso::

        class MiVista(RoleRequiredMixin, ListView):
            roles_permitidos = ["DOCENTE", "DIRECTIVO"]
    """

    roles_permitidos: list[str] = []

    def test_func(self):
        usuario = self.request.user
        if not usuario.is_authenticated:
            return False
        if usuario.is_superuser:
            return True
        return usuario.rol_principal in self.roles_permitidos

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("No tienes permiso para acceder a esta sección.")
        return super().handle_no_permission()


class PlantelFilterMixin:
    """Filtra el queryset por los planteles a los que tiene acceso el usuario."""

    plantel_field = "plantel"

    def get_queryset(self):
        qs = super().get_queryset()
        usuario = self.request.user
        if usuario.is_superuser:
            return qs
        filtro = {f"{self.plantel_field}__in": usuario.planteles.all()}
        return qs.filter(**filtro)
