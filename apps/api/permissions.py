"""Permisos personalizados para la API REST (app móvil GPS / terminal
biométrica)."""
from rest_framework import permissions

from apps.asistencia.models import DispositivoBiometrico
from apps.core.models import Usuario


class EsDispositivoBiometrico(permissions.BasePermission):
    """Permite el acceso únicamente a peticiones autenticadas como una
    terminal biométrica (ver `apps.api.authentication.DispositivoAPIKeyAuthentication`)."""

    message = "Esta acción requiere autenticación de dispositivo biométrico."

    def has_permission(self, request, view):
        return isinstance(request.auth, DispositivoBiometrico)


class EsAlumnoODocente(permissions.BasePermission):
    """Permite el acceso únicamente a usuarios autenticados con rol ALUMNO o
    DOCENTE (quienes reportan su propia ubicación GPS)."""

    message = "Esta acción requiere un usuario con rol de alumno o docente."

    def has_permission(self, request, view):
        usuario = request.user
        return bool(
            usuario
            and usuario.is_authenticated
            and usuario.rol_principal in (Usuario.Rol.ALUMNO, Usuario.Rol.DOCENTE)
        )
