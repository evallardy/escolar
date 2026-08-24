"""Endpoints DRF consumidos por la futura app móvil (reporte de ubicación GPS
de alumnos/docentes) y por las terminales biométricas (marcaje de entrada y
salida). Ver docs/DISENO.md sección de Asistencia y Seguridad (rate limiting)."""
from django.utils import timezone
from rest_framework import generics
from rest_framework.exceptions import Throttled

from apps.asistencia.models import ParametroGPS, RegistroAsistencia, UbicacionGPS
from apps.core.models import Usuario

from .authentication import DispositivoAPIKeyAuthentication
from .permissions import EsAlumnoODocente, EsDispositivoBiometrico
from .serializers import (
    MarcajeBiometricoSerializer,
    RegistroAsistenciaSerializer,
    UbicacionGPSSerializer,
)


def _plantel_de_persona(usuario):
    """Obtiene el plantel principal de un alumno o docente, o None si no
    tiene perfil vinculado / plantel asignado."""
    if usuario.rol_principal == Usuario.Rol.ALUMNO:
        alumno = getattr(usuario, "perfil_alumno", None)
        return alumno.plantel if alumno else None
    if usuario.rol_principal == Usuario.Rol.DOCENTE:
        docente = getattr(usuario, "perfil_docente", None)
        return docente.planteles.first() if docente else None
    return None


class UbicacionGPSListCreateView(generics.ListCreateAPIView):
    """GET: últimas ubicaciones propias reportadas.
    POST: la app móvil reporta un nuevo punto de ubicación."""

    serializer_class = UbicacionGPSSerializer
    permission_classes = [EsAlumnoODocente]
    throttle_scope = "gps"

    def get_queryset(self):
        return UbicacionGPS.objects.filter(persona=self.request.user).order_by(
            "-timestamp"
        )[:100]

    def perform_create(self, serializer):
        usuario = self.request.user
        plantel = _plantel_de_persona(usuario)

        # Rate limiting de negocio: no aceptar reportes más seguidos que el
        # intervalo configurado para el plantel (mínimo global en settings).
        intervalo_minutos = None
        if plantel is not None:
            parametro = (
                ParametroGPS.objects.vigentes().filter(plantel=plantel).first()
            )
            if parametro is not None:
                intervalo_minutos = parametro.intervalo_minutos

        if intervalo_minutos:
            ultima = (
                UbicacionGPS.objects.filter(persona=usuario)
                .order_by("-timestamp")
                .first()
            )
            if ultima is not None:
                segundos_transcurridos = (
                    timezone.now() - ultima.timestamp
                ).total_seconds()
                if segundos_transcurridos < intervalo_minutos * 60:
                    raise Throttled(
                        detail=(
                            "Se recibió un reporte de ubicación hace menos de "
                            f"{intervalo_minutos} minuto(s); espera antes de "
                            "reportar de nuevo."
                        )
                    )

        latitud = serializer.validated_data["latitud"]
        longitud = serializer.validated_data["longitud"]
        dentro_del_plantel = (
            plantel.esta_dentro_de_geocerca(latitud, longitud)
            if plantel is not None
            else False
        )
        serializer.save(persona=usuario, dentro_del_plantel=dentro_del_plantel)


class MarcajeBiometricoView(generics.CreateAPIView):
    """La terminal biométrica reporta un evento de entrada/salida."""

    serializer_class = MarcajeBiometricoSerializer
    authentication_classes = [DispositivoAPIKeyAuthentication]
    permission_classes = [EsDispositivoBiometrico]
    throttle_scope = "biometrico"

    def perform_create(self, serializer):
        dispositivo = self.request.auth
        serializer.save(
            dispositivo=dispositivo,
            origen=RegistroAsistencia.Origen.BIOMETRICO,
            fecha_hora=serializer.validated_data.get("fecha_hora") or timezone.now(),
        )


class MisRegistrosAsistenciaView(generics.ListAPIView):
    """Historial reciente de asistencia del propio usuario (alumno/docente),
    útil para que la app móvil muestre su bitácora de entradas/salidas."""

    serializer_class = RegistroAsistenciaSerializer
    permission_classes = [EsAlumnoODocente]

    def get_queryset(self):
        return RegistroAsistencia.objects.filter(persona=self.request.user).order_by(
            "-fecha_hora"
        )[:50]
