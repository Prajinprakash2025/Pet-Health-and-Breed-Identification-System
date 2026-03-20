from django.urls import path

from .views import AdminLoginView, UserLoginView, UserLogoutView, edit_profile, profile, register


urlpatterns = [
    # Normal user login/logout/register
    path("login/", UserLoginView.as_view(), name="login"),
    path("logout/", UserLogoutView.as_view(), name="logout"),
    path("register/", register, name="register"),

    # Profile pages
    path("profile/", profile, name="profile"),
    path("profile/edit/", edit_profile, name="profile_edit"),

    # Admin/staff login entry (redirects staff to ML admin dashboard)
    path("admin-login/", AdminLoginView.as_view(), name="admin_login"),
]
