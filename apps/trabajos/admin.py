from django.contrib import admin

from .models import EntregaTrabajo, Tarea


class EntregaTrabajoInline(admin.TabularInline):
    model = EntregaTrabajo
    extra = 0
    autocomplete_fields = ("alumno",)


@admin.register(Tarea)
class TareaAdmin(admin.ModelAdmin):
    list_display = ("titulo", "grupo", "docente", "fecha_entrega", "activa")
    list_filter = ("activa", "grupo")
    search_fields = ("titulo", "grupo__clave")
    autocomplete_fields = ("grupo", "docente")
    inlines = [EntregaTrabajoInline]


@admin.register(EntregaTrabajo)
class EntregaTrabajoAdmin(admin.ModelAdmin):
    list_display = ("alumno", "tarea", "fecha_entrega", "calificacion", "entregado_tarde")
    list_filter = ("tarea__grupo",)
    search_fields = ("alumno__matricula", "tarea__titulo")
    autocomplete_fields = ("tarea", "alumno")

    @admin.display(boolean=True, description="Tarde")
    def entregado_tarde(self, obj):
        return obj.entregado_tarde
