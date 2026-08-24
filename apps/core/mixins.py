"""Mixins reutilizables por todas las vistas CBV del proyecto:

- ``AjaxTemplateMixin``: permite que una misma vista responda la página
  completa (extiende base.html) o solo el fragmento parcial cuando la
  petición viene por AJAX (fetch), evitando duplicar lógica de contexto.
- ``RoleRequiredMixin``: protege una vista a un conjunto de roles.
- ``AjaxModalFormMixin``: patrón CRUD estándar del proyecto para
  Create/Update: el formulario se abre en un modal (AJAX) y al guardar con
  éxito responde JSON en lugar de redirigir, para que el JS cierre el modal
  y refresque la lista.
- ``AjaxDeleteView``: vista genérica de borrado (solo POST) que responde
  JSON, usada por el botón "Eliminar" de cada renglón de las listas CRUD.
"""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.views.generic import View
from django.views.generic.detail import SingleObjectMixin


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


class AjaxModalFormMixin(AjaxTemplateMixin):
    """Mixin para CreateView/UpdateView usadas dentro del modal CRUD genérico.

    - GET por AJAX: responde solo ``template_name_ajax`` (el fragmento del
      formulario), para poblar el contenido del modal.
    - POST por AJAX válido: en vez de redirigir, responde
      ``{"ok": true}`` para que ``static/js/ajax.js`` cierre el modal y
      refresque la lista (ver ``data-refresh-url``/``data-refresh-target``
      en ``templates/partials/_modal_form_base.html``).
    - POST por AJAX inválido: vuelve a renderizar el fragmento del
      formulario con los errores (comportamiento por defecto de Django, ya
      cubierto por ``AjaxTemplateMixin.get_template_names``).
    """

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.is_ajax():
            return JsonResponse({"ok": True})
        return response


class AjaxDeleteView(LoginRequiredMixin, SingleObjectMixin, View):
    """Vista genérica de borrado por AJAX (solo POST).

    Responde ``{"ok": true}`` en éxito para que el JS refresque la lista.
    Usar junto con un mixin de permisos (p. ej. ``RoleRequiredMixin``) y
    definir ``model`` y, si aplica, sobreescribir ``get_queryset`` para
    limitar qué objetos puede borrar el usuario.
    """

    def post(self, request, *args, **kwargs):
        objeto = self.get_object()
        objeto.delete()
        return JsonResponse({"ok": True})
