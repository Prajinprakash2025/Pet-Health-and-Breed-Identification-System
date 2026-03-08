from django.urls import path

from .views import UserLoginView, UserLogoutView, edit_profile, profile, register


urlpatterns = [
    path("login/", UserLoginView.as_view(), name="login"),
    path("logout/", UserLogoutView.as_view(), name="logout"),
    path("register/", register, name="register"),
    path("profile/", profile, name="profile"),
    path("profile/edit/", edit_profile, name="profile_edit"),
]

