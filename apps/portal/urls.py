from django.urls import path

from . import views

app_name = "portal"

urlpatterns = [
    path("", views.DashboardRouterView.as_view(), name="dashboard_router"),
    path("generico/", views.DashboardGenericoView.as_view(), name="dashboard_generico"),
    path("padres/", views.DashboardPadresView.as_view(), name="dashboard_padres"),
    path("alumnos/", views.DashboardAlumnosView.as_view(), name="dashboard_alumnos"),
    path("docentes/", views.DashboardDocentesView.as_view(), name="dashboard_docentes"),
    path(
        "administrativos/",
        views.DashboardAdministrativosView.as_view(),
        name="dashboard_administrativos",
    ),
    path(
        "directivos/",
        views.DashboardDirectivosView.as_view(),
        name="dashboard_directivos",
    ),
]
