from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from apps.asistencia.models import RegistroAsistencia
from apps.core.mixins import AjaxTemplateMixin, RoleRequiredMixin
from apps.core.models import Usuario
from apps.finanzas.models import CargoAlumno, Pago
from apps.incidencias.models import Incidencia
from apps.inscripciones.models import Inscripcion
from apps.trabajos.models import Tarea


class DashboardRouterView(LoginRequiredMixin, View):
    """Redirige al dashboard correspondiente según el rol del usuario autenticado."""

    def get(self, request, *args, **kwargs):
        return redirect(reverse(request.user.dashboard_url_name()))


class DashboardGenericoView(LoginRequiredMixin, AjaxTemplateMixin, TemplateView):
    """Pantalla de respaldo para usuarios sin rol asignado (o superuser puro)."""

    template_name = "portal/dashboard_generico.html"
    template_name_ajax = "portal/partials/dashboard_generico_partial.html"


class DashboardPadresView(RoleRequiredMixin, AjaxTemplateMixin, TemplateView):
    roles_permitidos = [Usuario.Rol.PADRE]
    template_name = "portal/dashboard_padres.html"
    template_name_ajax = "portal/partials/dashboard_padres_partial.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tutor = getattr(self.request.user, "perfil_tutor", None)
        hijos_info = []
        if tutor is not None:
            for alumno in tutor.alumnos.select_related("usuario", "programa").all():
                cargos = CargoAlumno.objects.filter(
                    alumno=alumno, estatus__in=["PENDIENTE", "VENCIDO"]
                )
                saldo_total = sum((c.saldo_pendiente for c in cargos), start=0)
                ultimos_cardex = alumno.cardex.select_related("materia").order_by(
                    "-ciclo_escolar", "materia"
                )[:5]
                ultima_asistencia = RegistroAsistencia.objects.filter(
                    persona=alumno.usuario
                ).order_by("-fecha_hora")[:5]
                hijos_info.append(
                    {
                        "alumno": alumno,
                        "saldo_pendiente": saldo_total,
                        "cargos_pendientes": cargos.count(),
                        "cardex": ultimos_cardex,
                        "asistencia": ultima_asistencia,
                    }
                )
        context["hijos_info"] = hijos_info
        return context


class DashboardAlumnosView(RoleRequiredMixin, AjaxTemplateMixin, TemplateView):
    roles_permitidos = [Usuario.Rol.ALUMNO]
    template_name = "portal/dashboard_alumnos.html"
    template_name_ajax = "portal/partials/dashboard_alumnos_partial.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        alumno = getattr(self.request.user, "perfil_alumno", None)
        context["alumno"] = alumno
        if alumno is None:
            return context

        inscripcion = (
            Inscripcion.objects.filter(alumno=alumno)
            .order_by("-ciclo_escolar__fecha_inicio")
            .first()
        )
        materias_inscritas = []
        if inscripcion is not None:
            materias_inscritas = list(
                inscripcion.materias.select_related(
                    "grupo__materia", "grupo__ciclo_escolar"
                ).prefetch_related("grupo__horarios")
            )
        context["inscripcion"] = inscripcion
        context["materias_inscritas"] = materias_inscritas

        grupo_ids = [im.grupo_id for im in materias_inscritas]
        context["tareas_pendientes"] = (
            Tarea.objects.filter(grupo_id__in=grupo_ids, activa=True)
            .exclude(entregas__alumno=alumno)
            .select_related("grupo__materia")
            .order_by("fecha_entrega")[:8]
        )

        cardex_qs = alumno.cardex.select_related("materia", "ciclo_escolar")
        context["cardex_resumen"] = {
            "cursando": cardex_qs.filter(estatus="CURSANDO").count(),
            "aprobadas": cardex_qs.filter(estatus="APROBADA").count(),
            "reprobadas": cardex_qs.filter(estatus="REPROBADA").count(),
        }
        context["cardex_reciente"] = cardex_qs.order_by(
            "-ciclo_escolar", "materia"
        )[:8]

        cargos = CargoAlumno.objects.filter(
            alumno=alumno, estatus__in=["PENDIENTE", "VENCIDO"]
        ).select_related("concepto")
        context["cargos_pendientes"] = cargos
        context["saldo_total"] = sum((c.saldo_pendiente for c in cargos), start=0)
        return context


class DashboardDocentesView(RoleRequiredMixin, AjaxTemplateMixin, TemplateView):
    roles_permitidos = [Usuario.Rol.DOCENTE]
    template_name = "portal/dashboard_docentes.html"
    template_name_ajax = "portal/partials/dashboard_docentes_partial.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        docente = getattr(self.request.user, "perfil_docente", None)
        context["docente"] = docente
        if docente is None:
            return context

        asignaciones = docente.asignaciones.filter(activo=True).select_related(
            "grupo__materia", "grupo__ciclo_escolar"
        )
        context["asignaciones"] = asignaciones

        grupo_ids = [a.grupo_id for a in asignaciones]
        tareas = Tarea.objects.filter(docente=docente).select_related("grupo__materia")
        context["tareas"] = tareas.order_by("-fecha_entrega")[:8]
        context["entregas_por_calificar"] = (
            docente.tareas.filter(entregas__calificacion__isnull=True)
            .aggregate(total=Count("entregas"))["total"]
            or 0
        )
        context["total_grupos"] = len(grupo_ids)
        return context


class DashboardAdministrativosView(RoleRequiredMixin, AjaxTemplateMixin, TemplateView):
    roles_permitidos = [Usuario.Rol.ADMINISTRATIVO]
    template_name = "portal/dashboard_administrativos.html"
    template_name_ajax = "portal/partials/dashboard_administrativos_partial.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["inscripciones_activas"] = Inscripcion.objects.filter(
            estatus="INSCRITO"
        ).count()
        cargos_pendientes = CargoAlumno.objects.filter(
            estatus__in=["PENDIENTE", "VENCIDO"]
        )
        context["cargos_pendientes"] = cargos_pendientes.count()
        context["monto_por_cobrar"] = (
            cargos_pendientes.aggregate(total=Sum("monto"))["total"] or 0
        )
        context["incidencias_abiertas"] = Incidencia.objects.filter(
            estatus__in=["ABIERTA", "EN_SEGUIMIENTO"]
        ).count()
        return context


class DashboardDirectivosView(RoleRequiredMixin, AjaxTemplateMixin, TemplateView):
    roles_permitidos = [Usuario.Rol.DIRECTIVO]
    template_name = "portal/dashboard_directivos.html"
    template_name_ajax = "portal/partials/dashboard_directivos_partial.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["matricula_total"] = Inscripcion.objects.filter(
            estatus="INSCRITO"
        ).values("alumno").distinct().count()

        hoy = timezone.localdate()
        primer_dia_mes = hoy.replace(day=1)
        context["cobranza_mes"] = (
            Pago.objects.filter(fecha_pago__gte=primer_dia_mes, fecha_pago__lte=hoy)
            .aggregate(total=Sum("monto"))["total"]
            or 0
        )

        registros_hoy = RegistroAsistencia.objects.filter(
            fecha_hora__date=hoy, tipo="ENTRADA"
        )
        context["asistencia_hoy"] = registros_hoy.values("persona").distinct().count()

        context["incidencias_abiertas"] = Incidencia.objects.filter(
            estatus__in=["ABIERTA", "EN_SEGUIMIENTO"]
        ).count()
        return context

