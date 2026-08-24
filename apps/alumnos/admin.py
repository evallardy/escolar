from django.contrib import admin

from .models import AlumnoTutor, Alumno, Cardex, DocumentoAlumno, Tutor


class AlumnoTutorInline(admin.TabularInline):
    model = AlumnoTutor
    extra = 0
    autocomplete_fields = ("tutor",)


class DocumentoAlumnoInline(admin.TabularInline):
    model = DocumentoAlumno
    extra = 0
    fields = ("tipo_documento", "archivo", "verificado")


class CardexInline(admin.TabularInline):
    model = Cardex
    extra = 0
    autocomplete_fields = ("materia", "grupo", "ciclo_escolar")


@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    list_display = ("matricula", "__str__", "programa", "plantel", "estatus")
    list_filter = ("programa", "plantel", "estatus")
    search_fields = (
        "matricula",
        "usuario__first_name",
        "usuario__last_name",
        "usuario__username",
        "curp",
    )
    autocomplete_fields = ("usuario", "plantel", "programa", "plan_estudios")
    inlines = [AlumnoTutorInline, DocumentoAlumnoInline, CardexInline]


@admin.register(Tutor)
class TutorAdmin(admin.ModelAdmin):
    list_display = ("__str__", "telefono", "ocupacion")
    search_fields = ("usuario__first_name", "usuario__last_name", "usuario__username")
    autocomplete_fields = ("usuario",)
    inlines = [AlumnoTutorInline]


@admin.register(Cardex)
class CardexAdmin(admin.ModelAdmin):
    list_display = ("alumno", "materia", "ciclo_escolar", "calificacion", "estatus")
    list_filter = ("estatus", "ciclo_escolar")
    search_fields = ("alumno__matricula", "materia__nombre", "materia__clave")
    autocomplete_fields = ("alumno", "materia", "grupo", "ciclo_escolar")


@admin.register(DocumentoAlumno)
class DocumentoAlumnoAdmin(admin.ModelAdmin):
    list_display = ("alumno", "tipo_documento", "fecha_carga", "verificado")
    list_filter = ("tipo_documento", "verificado")
    search_fields = ("alumno__matricula",)
    autocomplete_fields = ("alumno",)
