from django.contrib import admin

from .models import Inscripcion, InscripcionMateria


class InscripcionMateriaInline(admin.TabularInline):
    model = InscripcionMateria
    extra = 0
    autocomplete_fields = ("grupo",)


@admin.register(Inscripcion)
class InscripcionAdmin(admin.ModelAdmin):
    list_display = ("alumno", "programa", "ciclo_escolar", "estatus", "fecha_inscripcion")
    list_filter = ("ciclo_escolar", "programa", "estatus")
    search_fields = ("alumno__matricula", "alumno__usuario__first_name", "alumno__usuario__last_name")
    autocomplete_fields = ("alumno", "programa", "ciclo_escolar")
    inlines = [InscripcionMateriaInline]


@admin.register(InscripcionMateria)
class InscripcionMateriaAdmin(admin.ModelAdmin):
    list_display = ("inscripcion", "grupo", "estatus", "calificacion_final")
    list_filter = ("estatus",)
    search_fields = ("inscripcion__alumno__matricula", "grupo__clave")
    autocomplete_fields = ("inscripcion", "grupo")
