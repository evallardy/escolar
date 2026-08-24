from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("login/", views.LoginEscolarView.as_view(), name="login"),
    path("logout/", views.LogoutEscolarView.as_view(), name="logout"),
]
