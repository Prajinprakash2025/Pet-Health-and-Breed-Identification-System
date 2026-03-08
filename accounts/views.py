from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from .forms import RegistrationForm, UserProfileForm, LoginForm
from .models import UserProfile


class UserLoginView(LoginView):
    template_name = "accounts/login.html"
    form_class = LoginForm


class UserLogoutView(LogoutView):
    next_page = reverse_lazy("home")


def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = RegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


@login_required
def profile(request):
    profile_obj, _ = UserProfile.objects.get_or_create(user=request.user)
    return render(request, "accounts/profile.html", {"profile": profile_obj})


@login_required
def edit_profile(request):
    profile_obj, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=profile_obj)
        if form.is_valid():
            form.save()
            return redirect("accounts:profile")
    else:
        form = UserProfileForm(instance=profile_obj)
    return render(request, "accounts/profile_edit.html", {"form": form})

