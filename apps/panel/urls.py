from django.urls import path

from . import views

app_name = "panel"

urlpatterns = [
    path("", views.PanelIndexView.as_view(), name="index"),
    path("<str:app_label>/<str:model_name>/", views.PanelListView.as_view(), name="listado"),
    path("<str:app_label>/<str:model_name>/agregar/", views.PanelCreateUpdateView.as_view(), name="agregar"),
    path("<str:app_label>/<str:model_name>/<int:pk>/editar/", views.PanelCreateUpdateView.as_view(), name="editar"),
    path("<str:app_label>/<str:model_name>/<int:pk>/eliminar/", views.PanelDeleteView.as_view(), name="eliminar"),
]
