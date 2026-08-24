"""Serializers de la API REST: reporte de ubicación GPS (app móvil) y
marcaje de asistencia (terminal biométrica)."""
from rest_framework import serializers

from apps.asistencia.models import RegistroAsistencia, UbicacionGPS
from apps.core.models import Usuario


class UbicacionGPSSerializer(serializers.ModelSerializer):
    """Ubicación reportada por la app móvil de un alumno/docente.

    `persona` se asigna automáticamente al usuario autenticado (nunca se
    confía en un valor enviado por el cliente) y `dentro_del_plantel` lo
    calcula el backend, no el cliente.
    """

    class Meta:
        model = UbicacionGPS
        fields = ["id", "latitud", "longitud", "timestamp", "dentro_del_plantel"]
        read_only_fields = ["id", "timestamp", "dentro_del_plantel"]


class RegistroAsistenciaSerializer(serializers.ModelSerializer):
    dispositivo = serializers.StringRelatedField()

    class Meta:
        model = RegistroAsistencia
        fields = ["id", "persona", "dispositivo", "fecha_hora", "tipo", "origen"]
        read_only_fields = fields


class MarcajeBiometricoSerializer(serializers.ModelSerializer):
    """Evento de marcaje (entrada/salida) enviado por una terminal
    biométrica. `dispositivo` y `origen` los asigna la vista a partir del
    dispositivo autenticado, no del payload."""

    persona = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.filter(
            rol_principal__in=[Usuario.Rol.ALUMNO, Usuario.Rol.DOCENTE]
        )
    )

    class Meta:
        model = RegistroAsistencia
        fields = ["id", "persona", "fecha_hora", "tipo"]
        read_only_fields = ["id"]
        extra_kwargs = {
            "fecha_hora": {"required": False},
        }
