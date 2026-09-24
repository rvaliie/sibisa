from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register_warga, name="register"),
    path("login/", auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("redirect-after-login/", views.redirect_after_login, name="redirect_after_login"),
    path("buat-validator/", views.buat_validator, name="buat_validator"),
]
