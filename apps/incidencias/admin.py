from django.contrib import admin

from .models import Incidencia, SeguimientoIncidencia, TipoIncidencia


@admin.register(TipoIncidencia)
class TipoIncidenciaAdmin(admin.ModelAdmin):
    list_display = ("clave", "nombre", "gravedad", "activo")
    list_filter = ("gravedad", "activo")
    search_fields = ("clave", "nombre")


class SeguimientoIncidenciaInline(admin.TabularInline):
    model = SeguimientoIncidencia
    extra = 0
    readonly_fields = ("fecha",)
    autocomplete_fields = ("usuario",)


@admin.register(Incidencia)
class IncidenciaAdmin(admin.ModelAdmin):
    list_display = ("persona_involucrada", "tipo", "fecha", "estatus", "registrado_por")
    list_filter = ("estatus", "tipo")
    search_fields = (
        "persona_involucrada__first_name",
        "persona_involucrada__last_name",
        "persona_involucrada__username",
    )
    autocomplete_fields = ("persona_involucrada", "tipo", "registrado_por")
    date_hierarchy = "fecha"
    inlines = [SeguimientoIncidenciaInline]
