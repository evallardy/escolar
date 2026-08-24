from django.contrib import admin

from .models import Empleado, PeriodoNomina, Puesto, ReciboNomina


@admin.register(Puesto)
class PuestoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "plantel", "sueldo_base")
    list_filter = ("plantel",)
    search_fields = ("nombre",)
    autocomplete_fields = ("plantel",)


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ("__str__", "puesto", "rfc", "activo")
    list_filter = ("puesto", "activo")
    search_fields = (
        "usuario__first_name",
        "usuario__last_name",
        "usuario__username",
        "rfc",
    )
    autocomplete_fields = ("usuario", "puesto")


@admin.register(PeriodoNomina)
class PeriodoNominaAdmin(admin.ModelAdmin):
    list_display = ("__str__", "tipo", "fecha_inicio", "fecha_fin", "cerrado")
    list_filter = ("tipo", "cerrado")
    search_fields = ("fecha_inicio", "fecha_fin")


@admin.register(ReciboNomina)
class ReciboNominaAdmin(admin.ModelAdmin):
    list_display = (
        "empleado",
        "periodo",
        "percepciones",
        "deducciones",
        "neto",
        "estatus_timbrado",
    )
    list_filter = ("estatus_timbrado", "periodo")
    search_fields = ("empleado__usuario__first_name", "empleado__usuario__last_name", "uuid_cfdi")
    autocomplete_fields = ("empleado", "periodo")
    readonly_fields = ("neto",)
