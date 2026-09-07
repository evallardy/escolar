"""Vistas genéricas del Panel Ejecutivo: un único juego de vistas (index,
listado, alta, edición, borrado) que sirve a los 28 modelos registrados en
``registry.py``, resuelto dinámicamente por ``app_label``/``model_name`` en
la URL — el mismo patrón que usa ``django.contrib.admin`` internamente."""
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import TemplateView, View

from apps.academico.models import Programa
from apps.alumnos.models import Alumno
from apps.core.mixins import RoleRequiredMixin
from apps.core.models import Plantel, Usuario
from apps.docentes.models import Docente
from apps.nomina.models import Empleado

from .forms import obtener_form_class
from .registry import configs_por_modulo, obtener_config
from .utils import construir_filas, construir_filtros, etiqueta_campo

ROLES_PANEL = [Usuario.Rol.DIRECTIVO]


class PanelBaseMixin(RoleRequiredMixin):
    roles_permitidos = ROLES_PANEL


class PanelIndexView(PanelBaseMixin, TemplateView):
    template_name = "panel/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        modulos = list(configs_por_modulo().values())
        for modulo in modulos:
            modulo["modelos"] = [
                {"config": cfg, "total": cfg.model.objects.count()} for cfg in modulo["modelos"]
            ]
        context["modulos"] = modulos
        context["kpis"] = [
            {"etiqueta": "Alumnos activos", "valor": Alumno.objects.filter(estatus=Alumno.Estatus.ACTIVO).count(), "icono": "bi-mortarboard"},
            {"etiqueta": "Docentes", "valor": Docente.objects.filter(activo=True).count(), "icono": "bi-person-workspace"},
            {"etiqueta": "Personal (nómina)", "valor": Empleado.objects.filter(activo=True).count(), "icono": "bi-people"},
            {"etiqueta": "Programas académicos", "valor": Programa.objects.filter(activo=True).count(), "icono": "bi-diagram-3"},
            {"etiqueta": "Planteles", "valor": Plantel.objects.filter(activo=True).count(), "icono": "bi-building"},
        ]
        return context


class PanelListView(PanelBaseMixin, View):
    template_name = "panel/list.html"

    def get(self, request, app_label, model_name):
        config = obtener_config(app_label, model_name)
        queryset = config.model.objects.all()
        if config.select_related:
            queryset = queryset.select_related(*config.select_related)
        if config.ordering:
            queryset = queryset.order_by(*config.ordering)
        elif not config.model._meta.ordering:
            # Evita advertencias de paginación con querysets sin orden definido.
            queryset = queryset.order_by("pk")

        filtros, lookups_activos = construir_filtros(config.model, config.list_filter, request.GET)
        if lookups_activos:
            queryset = queryset.filter(**lookups_activos)

        termino = request.GET.get("q", "").strip()
        if termino and config.search_fields:
            condicion = Q()
            for campo in config.search_fields:
                condicion |= Q(**{f"{campo}__icontains": termino})
            queryset = queryset.filter(condicion)

        columnas = [etiqueta_campo(config.model, nombre) for nombre in config.list_display]
        total = queryset.count()
        paginador = Paginator(queryset, 25)
        pagina = paginador.get_page(request.GET.get("pagina"))
        filas = construir_filas(pagina.object_list, config.list_display)

        parametros_sin_pagina = request.GET.copy()
        parametros_sin_pagina.pop("pagina", None)

        context = {
            "config": config,
            "columnas": columnas,
            "filas": filas,
            "filtros": filtros,
            "termino": termino,
            "total": total,
            "pagina": pagina,
            "query_extra": parametros_sin_pagina.urlencode(),
        }
        return render(request, self.template_name, context)


class PanelFormMixin(PanelBaseMixin):
    template_name = "panel/form.html"

    def get_config(self):
        return obtener_config(self.kwargs["app_label"], self.kwargs["model_name"])

    def get_instancia(self, config):
        pk = self.kwargs.get("pk")
        if pk is None:
            return config.model()
        return get_object_or_404(config.model, pk=pk)

    def render_formulario(self, request, config, form, instancia):
        context = {
            "config": config,
            "form": form,
            "instancia": instancia,
            "es_nuevo": instancia.pk is None,
        }
        return render(request, self.template_name, context)


class PanelCreateUpdateView(PanelFormMixin, View):
    def get(self, request, app_label, model_name, pk=None):
        config = self.get_config()
        instancia = self.get_instancia(config)
        form_class = obtener_form_class(config)
        form = form_class(instance=instancia)
        return self.render_formulario(request, config, form, instancia)

    def post(self, request, app_label, model_name, pk=None):
        config = self.get_config()
        instancia = self.get_instancia(config)
        form_class = obtener_form_class(config)
        form = form_class(request.POST, request.FILES, instance=instancia)
        if form.is_valid():
            form.save()
            verbo = "creado" if instancia.pk is None else "actualizado"
            messages.success(request, f"{config.verbose_name} {verbo} correctamente.")
            return redirect(reverse("panel:listado", args=[app_label, model_name]))
        return self.render_formulario(request, config, form, instancia)


class PanelDeleteView(PanelBaseMixin, View):
    template_name = "panel/confirm_delete.html"

    def get(self, request, app_label, model_name, pk):
        config = obtener_config(app_label, model_name)
        instancia = get_object_or_404(config.model, pk=pk)
        return render(request, self.template_name, {"config": config, "instancia": instancia})

    def post(self, request, app_label, model_name, pk):
        config = obtener_config(app_label, model_name)
        instancia = get_object_or_404(config.model, pk=pk)
        instancia.delete()
        messages.success(request, f"{config.verbose_name} eliminado correctamente.")
        return redirect(reverse("panel:listado", args=[app_label, model_name]))
