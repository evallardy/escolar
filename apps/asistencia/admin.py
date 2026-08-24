from django.contrib import admin

from .models import DispositivoBiometrico, ParametroGPS, RegistroAsistencia, UbicacionGPS


@admin.register(DispositivoBiometrico)
class DispositivoBiometricoAdmin(admin.ModelAdmin):
    list_display = ("identificador", "marca", "modelo", "plantel", "ubicacion", "activo")
    list_filter = ("plantel", "activo")
    search_fields = ("identificador", "marca", "modelo")
    autocomplete_fields = ("plantel",)


@admin.register(RegistroAsistencia)
class RegistroAsistenciaAdmin(admin.ModelAdmin):
    list_display = ("persona", "tipo", "origen", "fecha_hora", "dispositivo")
    list_filter = ("tipo", "origen", "dispositivo")
    search_fields = (
        "persona__username",
        "persona__first_name",
        "persona__last_name",
    )
    autocomplete_fields = ("persona", "dispositivo", "registrado_por")
    date_hierarchy = "fecha_hora"


@admin.register(ParametroGPS)
class ParametroGPSAdmin(admin.ModelAdmin):
    list_display = ("plantel", "intervalo_minutos", "activo")
    autocomplete_fields = ("plantel",)


@admin.register(UbicacionGPS)
class UbicacionGPSAdmin(admin.ModelAdmin):
    list_display = ("persona", "latitud", "longitud", "dentro_del_plantel", "timestamp")
    list_filter = ("dentro_del_plantel",)
    search_fields = ("persona__username", "persona__first_name", "persona__last_name")
    autocomplete_fields = ("persona",)
    date_hierarchy = "timestamp"
