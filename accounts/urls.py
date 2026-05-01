from django.urls import path
from django.urls import reverse_lazy
from django.contrib.auth.views import (
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)

from .views import AdminLoginView, UserLoginView, logout_user, edit_profile, profile, register


urlpatterns = [
    # Normal user login/logout/register
    path("login/", UserLoginView.as_view(), name="login"),
    path("logout/", logout_user, name="logout"),
    path("register/", register, name="register"),
    path(
        "password-reset/",
        PasswordResetView.as_view(
            template_name="accounts/password_reset_form.html",
            email_template_name="accounts/password_reset_email.html",
            subject_template_name="accounts/password_reset_subject.txt",
            success_url=reverse_lazy("accounts:password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        PasswordResetDoneView.as_view(template_name="accounts/password_reset_done.html"),
        name="password_reset_done",
    ),
    path(
        "password-reset/<uidb64>/<token>/",
        PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html",
            success_url=reverse_lazy("accounts:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "password-reset/complete/",
        PasswordResetCompleteView.as_view(template_name="accounts/password_reset_complete.html"),
        name="password_reset_complete",
    ),

    # Profile pages
    path("profile/", profile, name="profile"),
    path("profile/edit/", edit_profile, name="profile_edit"),

    # Admin/staff login entry (redirects staff to ML admin dashboard)
    path("admin-login/", AdminLoginView.as_view(), name="admin_login"),
]
