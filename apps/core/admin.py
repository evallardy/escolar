from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Plantel, Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Información escolar", {"fields": ("rol_principal", "planteles", "telefono", "foto")}),
    )
    list_display = ("username", "get_full_name", "rol_principal", "is_active", "is_staff")
    list_filter = UserAdmin.list_filter + ("rol_principal",)
    filter_horizontal = UserAdmin.filter_horizontal + ("planteles",)


@admin.register(Plantel)
class PlantelAdmin(admin.ModelAdmin):
    list_display = ("clave", "nombre", "activo")
    search_fields = ("clave", "nombre")
    list_filter = ("activo",)
