from django.contrib import admin

from .models import AsignacionDocente, Docente


class AsignacionDocenteInline(admin.TabularInline):
    model = AsignacionDocente
    extra = 0
    autocomplete_fields = ("grupo",)


@admin.register(Docente)
class DocenteAdmin(admin.ModelAdmin):
    list_display = (
        "__str__",
        "numero_empleado",
        "especialidad",
        "nivel_estudios",
        "activo",
    )
    list_filter = ("nivel_estudios", "activo", "planteles")
    search_fields = (
        "numero_empleado",
        "usuario__first_name",
        "usuario__last_name",
        "usuario__username",
        "rfc",
        "curp",
    )
    autocomplete_fields = ("usuario",)
    filter_horizontal = ("planteles",)
    inlines = [AsignacionDocenteInline]


@admin.register(AsignacionDocente)
class AsignacionDocenteAdmin(admin.ModelAdmin):
    list_display = ("docente", "grupo", "fecha_inicio", "fecha_fin", "activo")
    list_filter = ("activo",)
    search_fields = ("docente__usuario__first_name", "docente__usuario__last_name", "grupo__clave")
    autocomplete_fields = ("docente", "grupo")
