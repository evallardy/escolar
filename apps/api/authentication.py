"""Autenticación de dispositivos (terminales biométricas) para la API REST.

Las terminales biométricas no son un `Usuario` del sistema: se identifican con
una clave secreta (`DispositivoBiometrico.clave_api`) generada al crear el
dispositivo desde el admin. La terminal debe enviar dos cabeceras:

    X-Device-Id:  identificador del dispositivo (DispositivoBiometrico.identificador)
    X-Device-Key: clave_api del dispositivo

Se usa `secrets.compare_digest` para evitar ataques de timing al comparar la
clave.
"""
import secrets

from rest_framework import authentication, exceptions

from apps.asistencia.models import DispositivoBiometrico


class DispositivoAPIKeyAuthentication(authentication.BaseAuthentication):
    """Autentica una terminal biométrica vía cabeceras X-Device-Id/X-Device-Key.

    En caso de éxito retorna `(None, dispositivo)`: no hay un `Usuario` de
    Django asociado (request.user queda anónimo), pero `request.auth` es la
    instancia de `DispositivoBiometrico`, lo que permite a las vistas y
    permisos identificar al dispositivo que hace la petición.
    """

    def authenticate(self, request):
        identificador = request.headers.get("X-Device-Id")
        clave = request.headers.get("X-Device-Key")
        if not identificador or not clave:
            return None

        try:
            dispositivo = DispositivoBiometrico.objects.get(
                identificador=identificador, activo=True
            )
        except DispositivoBiometrico.DoesNotExist as exc:
            raise exceptions.AuthenticationFailed(
                "Dispositivo no reconocido o inactivo."
            ) from exc

        if not secrets.compare_digest(dispositivo.clave_api, clave):
            raise exceptions.AuthenticationFailed("Clave de dispositivo inválida.")

        return (None, dispositivo)

    def authenticate_header(self, request):
        return "X-Device-Key"
