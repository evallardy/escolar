from django.contrib import admin

from .models import Beca, CargoAlumno, ConceptoCobro, Pago


@admin.register(ConceptoCobro)
class ConceptoCobroAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "plantel",
        "programa",
        "periodicidad",
        "monto",
        "activo",
        "esta_vigente",
    )
    list_filter = ("plantel", "periodicidad", "activo")
    search_fields = ("nombre",)
    autocomplete_fields = ("plantel", "programa")

    @admin.display(boolean=True, description="Vigente")
    def esta_vigente(self, obj):
        return obj.esta_vigente


class PagoInline(admin.TabularInline):
    model = Pago
    extra = 0
    readonly_fields = ("fecha_registro",)


@admin.register(CargoAlumno)
class CargoAlumnoAdmin(admin.ModelAdmin):
    list_display = (
        "alumno",
        "concepto",
        "ciclo_escolar",
        "monto",
        "saldo_pendiente",
        "fecha_limite",
        "estatus",
    )
    list_filter = ("estatus", "ciclo_escolar", "concepto")
    search_fields = ("alumno__matricula", "concepto__nombre")
    autocomplete_fields = ("alumno", "concepto", "ciclo_escolar")
    inlines = [PagoInline]


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ("cargo", "monto", "fecha_pago", "forma_pago", "origen")
    list_filter = ("forma_pago", "origen")
    search_fields = ("cargo__alumno__matricula", "referencia_transaccion")
    autocomplete_fields = ("cargo", "capturado_por")


@admin.register(Beca)
class BecaAdmin(admin.ModelAdmin):
    list_display = ("alumno", "concepto", "tipo", "valor", "activo")
    list_filter = ("tipo", "activo")
    search_fields = ("alumno__matricula", "motivo")
    autocomplete_fields = ("alumno", "concepto")
