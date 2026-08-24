from django.contrib.auth.views import LoginView, LogoutView


class LoginEscolarView(LoginView):
    template_name = "core/login.html"
    redirect_authenticated_user = True


class LogoutEscolarView(LogoutView):
    next_page = "core:login"
