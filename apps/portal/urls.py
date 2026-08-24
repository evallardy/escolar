from django.urls import path

from . import views, views_alumnos, views_docentes, views_finanzas, views_incidencias

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

    # --- Docentes: tareas y calificación de entregas -----------------------
    path("docentes/tareas/", views_docentes.TareaListView.as_view(), name="docente_tareas_lista"),
    path("docentes/tareas/nueva/", views_docentes.TareaCreateView.as_view(), name="docente_tarea_crear"),
    path("docentes/tareas/<int:pk>/editar/", views_docentes.TareaUpdateView.as_view(), name="docente_tarea_editar"),
    path("docentes/tareas/<int:pk>/eliminar/", views_docentes.TareaDeleteView.as_view(), name="docente_tarea_eliminar"),
    path("docentes/tareas/<int:tarea_pk>/entregas/", views_docentes.EntregaListView.as_view(), name="docente_entregas_lista"),
    path("docentes/entregas/<int:pk>/calificar/", views_docentes.EntregaCalificarView.as_view(), name="docente_entrega_calificar"),

    # --- Alumnos: tareas y entregas propias ---------------------------------
    path("alumnos/tareas/", views_alumnos.AlumnoTareaListView.as_view(), name="alumno_tareas_lista"),
    path("alumnos/tareas/<int:tarea_pk>/entregar/", views_alumnos.EntregaCreateView.as_view(), name="alumno_entrega_crear"),
    path("alumnos/entregas/<int:pk>/editar/", views_alumnos.EntregaUpdateView.as_view(), name="alumno_entrega_editar"),
    path("alumnos/entregas/<int:pk>/eliminar/", views_alumnos.EntregaDeleteView.as_view(), name="alumno_entrega_eliminar"),

    # --- Administrativos: incidencias ---------------------------------------
    path("administrativos/incidencias/", views_incidencias.IncidenciaListView.as_view(), name="admin_incidencias_lista"),
    path("administrativos/incidencias/nueva/", views_incidencias.IncidenciaCreateView.as_view(), name="admin_incidencia_crear"),
    path("administrativos/incidencias/<int:pk>/editar/", views_incidencias.IncidenciaUpdateView.as_view(), name="admin_incidencia_editar"),
    path("administrativos/incidencias/<int:pk>/eliminar/", views_incidencias.IncidenciaDeleteView.as_view(), name="admin_incidencia_eliminar"),
    path("administrativos/incidencias/<int:incidencia_pk>/seguimientos/", views_incidencias.SeguimientoListView.as_view(), name="admin_seguimientos_lista"),
    path("administrativos/incidencias/<int:incidencia_pk>/seguimientos/nuevo/", views_incidencias.SeguimientoCreateView.as_view(), name="admin_seguimiento_crear"),

    # --- Administrativos: conceptos de cobro --------------------------------
    path("administrativos/conceptos-cobro/", views_finanzas.ConceptoCobroListView.as_view(), name="admin_conceptos_lista"),
    path("administrativos/conceptos-cobro/nuevo/", views_finanzas.ConceptoCobroCreateView.as_view(), name="admin_concepto_crear"),
    path("administrativos/conceptos-cobro/<int:pk>/editar/", views_finanzas.ConceptoCobroUpdateView.as_view(), name="admin_concepto_editar"),
    path("administrativos/conceptos-cobro/<int:pk>/eliminar/", views_finanzas.ConceptoCobroDeleteView.as_view(), name="admin_concepto_eliminar"),

    # --- Administrativos: cargos y pagos -------------------------------------
    path("administrativos/cargos/", views_finanzas.CargoAlumnoListView.as_view(), name="admin_cargos_lista"),
    path("administrativos/cargos/nuevo/", views_finanzas.CargoAlumnoCreateView.as_view(), name="admin_cargo_crear"),
    path("administrativos/cargos/<int:pk>/editar/", views_finanzas.CargoAlumnoUpdateView.as_view(), name="admin_cargo_editar"),
    path("administrativos/cargos/<int:pk>/eliminar/", views_finanzas.CargoAlumnoDeleteView.as_view(), name="admin_cargo_eliminar"),
    path("administrativos/cargos/<int:cargo_pk>/pagos/", views_finanzas.PagoListView.as_view(), name="admin_pagos_lista"),
    path("administrativos/cargos/<int:cargo_pk>/pagos/nuevo/", views_finanzas.PagoCreateView.as_view(), name="admin_pago_crear"),
    path("administrativos/pagos/<int:pk>/editar/", views_finanzas.PagoUpdateView.as_view(), name="admin_pago_editar"),
    path("administrativos/pagos/<int:pk>/eliminar/", views_finanzas.PagoDeleteView.as_view(), name="admin_pago_eliminar"),
]

