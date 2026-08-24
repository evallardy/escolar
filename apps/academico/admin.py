from django.contrib import admin

from .models import (
    CalendarioEvento,
    CicloEscolar,
    Grupo,
    HorarioClase,
    Materia,
    NivelEducativo,
    PlanEstudios,
    Programa,
)


@admin.register(NivelEducativo)
class NivelEducativoAdmin(admin.ModelAdmin):
    list_display = ("clave", "nombre", "orden", "activo", "esta_vigente")
    list_filter = ("activo",)
    search_fields = ("clave", "nombre")
    ordering = ("orden",)

    @admin.display(boolean=True, description="Vigente")
    def esta_vigente(self, obj):
        return obj.esta_vigente


class PlanEstudiosInline(admin.TabularInline):
    model = PlanEstudios
    extra = 0
    fields = ("version", "total_creditos", "vigente_desde", "vigente_hasta", "activo")


@admin.register(Programa)
class ProgramaAdmin(admin.ModelAdmin):
    list_display = ("clave", "nombre", "nivel", "plantel", "modalidad", "activo")
    list_filter = ("nivel", "plantel", "modalidad", "activo")
    search_fields = ("clave", "nombre")
    autocomplete_fields = ("nivel", "plantel")
    inlines = [PlanEstudiosInline]


class MateriaInline(admin.TabularInline):
    model = Materia
    extra = 0
    fields = ("clave", "nombre", "periodo", "creditos", "tipo", "activo")


@admin.register(PlanEstudios)
class PlanEstudiosAdmin(admin.ModelAdmin):
    list_display = ("programa", "version", "total_creditos", "activo")
    list_filter = ("programa__nivel", "activo")
    search_fields = ("programa__nombre", "version")
    autocomplete_fields = ("programa",)
    inlines = [MateriaInline]


@admin.register(Materia)
class MateriaAdmin(admin.ModelAdmin):
    list_display = ("clave", "nombre", "plan_estudios", "periodo", "creditos", "tipo", "activo")
    list_filter = ("plan_estudios__programa", "tipo", "activo")
    search_fields = ("clave", "nombre")
    autocomplete_fields = ("plan_estudios",)
    filter_horizontal = ("seriacion",)


class CalendarioEventoInline(admin.TabularInline):
    model = CalendarioEvento
    extra = 0
    fields = ("nombre", "tipo", "fecha_inicio", "fecha_fin")


@admin.register(CicloEscolar)
class CicloEscolarAdmin(admin.ModelAdmin):
    list_display = ("clave", "nombre", "plantel", "fecha_inicio", "fecha_fin", "activo")
    list_filter = ("plantel", "activo")
    search_fields = ("clave", "nombre")
    inlines = [CalendarioEventoInline]


@admin.register(CalendarioEvento)
class CalendarioEventoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "ciclo_escolar", "tipo", "fecha_inicio", "fecha_fin")
    list_filter = ("tipo", "ciclo_escolar")
    search_fields = ("nombre",)
    autocomplete_fields = ("ciclo_escolar",)


class HorarioClaseInline(admin.TabularInline):
    model = HorarioClase
    extra = 0


@admin.register(Grupo)
class GrupoAdmin(admin.ModelAdmin):
    list_display = ("__str__", "materia", "ciclo_escolar", "turno", "cupo_maximo", "activo")
    list_filter = ("ciclo_escolar", "turno", "activo")
    search_fields = ("clave", "materia__nombre", "materia__clave")
    autocomplete_fields = ("ciclo_escolar", "materia")
    inlines = [HorarioClaseInline]
