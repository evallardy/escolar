from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token

from . import views

app_name = "api"

urlpatterns = [
    # Login de la app móvil: POST {username, password} -> {"token": "..."}
    path("token/", obtain_auth_token, name="obtener_token"),
    path(
        "gps/ubicaciones/",
        views.UbicacionGPSListCreateView.as_view(),
        name="gps_ubicaciones",
    ),
    path(
        "asistencia/marcaje/",
        views.MarcajeBiometricoView.as_view(),
        name="asistencia_marcaje",
    ),
    path(
        "asistencia/mis-registros/",
        views.MisRegistrosAsistenciaView.as_view(),
        name="asistencia_mis_registros",
    ),
]
