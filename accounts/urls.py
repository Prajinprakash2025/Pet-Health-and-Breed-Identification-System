from django.urls import path
from django.views.generic import TemplateView

from .views import (
    UserLoginView,
    edit_profile,
    login_verify,
    logout_user,
    password_reset_confirm,
    password_reset_request,
    password_reset_verify,
    profile,
    register,
    registration_verify,
)


urlpatterns = [
    # Normal user login/logout/register
    path("login/", UserLoginView.as_view(), name="login"),
    path("login/verify/", login_verify, name="login_verify"),
    path("logout/", logout_user, name="logout"),
    path("register/", register, name="register"),
    path("register/verify/", registration_verify, name="registration_verify"),
    path("password-reset/", password_reset_request, name="password_reset"),
    path("password-reset/verify/", password_reset_verify, name="password_reset_verify"),
    path("password-reset/done/", password_reset_verify, name="password_reset_done"),
    path("password-reset/new-password/", password_reset_confirm, name="password_reset_confirm"),
    path(
        "password-reset/complete/",
        TemplateView.as_view(template_name="accounts/password_reset_complete.html"),
        name="password_reset_complete",
    ),

    # Profile pages
    path("profile/", profile, name="profile"),
    path("profile/edit/", edit_profile, name="profile_edit"),
]
