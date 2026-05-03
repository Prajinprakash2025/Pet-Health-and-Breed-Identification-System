from datetime import timedelta
import secrets

from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from django.utils.dateparse import parse_datetime

from .forms import (
    LoginForm,
    PasswordResetEmailForm,
    PasswordResetNewPasswordForm,
    PasswordResetOTPForm,
    RegistrationForm,
    UserProfileForm,
)
from .models import UserProfile


User = get_user_model()
RESET_SESSION_KEYS = (
    "password_reset_user_id",
    "password_reset_email",
    "password_reset_otp",
    "password_reset_otp_expires_at",
    "password_reset_otp_verified",
    "password_reset_otp_attempts",
)
OTP_EXPIRY_MINUTES = 10
MAX_OTP_ATTEMPTS = 5


class UserLoginView(LoginView):
    template_name = "accounts/login.html"
    form_class = LoginForm


class AdminLoginView(LoginView):
    """
    Separate login entry point for admins/staff.

    Uses the same form and template as the normal login,
    but after successful login sends staff to the ML admin dashboard,
    and non-staff users to their profile.
    """

    template_name = "accounts/login.html"
    form_class = LoginForm

    def get_success_url(self):
        user = self.request.user
        # Staff or superuser users go to the ML admin dashboard.
        if user.is_staff or user.is_superuser:
            return reverse("analytics:ml_admin_dashboard")

        # Non-staff: still allow login but show a small message
        messages.info(self.request, "You are logged in as a regular user.")
        return reverse("accounts:profile")


def logout_user(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect("home")


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


def _clear_password_reset_session(request):
    for key in RESET_SESSION_KEYS:
        request.session.pop(key, None)


def _generate_otp():
    return f"{secrets.randbelow(1_000_000):06d}"


def _print_password_reset_otp(email, otp, expires_at):
    print("")
    print("========================================")
    print("PetCare AI password reset OTP")
    print(f"Email: {email}")
    print(f"OTP: {otp}")
    print(f"Expires at: {expires_at:%Y-%m-%d %H:%M:%S %Z}")
    print("========================================")
    print("")


def _get_reset_expiry(request):
    value = request.session.get("password_reset_otp_expires_at")
    if not value:
        return None
    expires_at = parse_datetime(value)
    if expires_at is None:
        return None
    if timezone.is_naive(expires_at):
        expires_at = timezone.make_aware(expires_at, timezone.get_current_timezone())
    return expires_at


def _otp_has_expired(request):
    expires_at = _get_reset_expiry(request)
    return expires_at is None or timezone.now() >= expires_at


def _get_pending_reset_user(request):
    user_id = request.session.get("password_reset_user_id")
    if not user_id:
        return None
    return User.objects.filter(pk=user_id, is_active=True).first()


def _masked_email(email):
    local, separator, domain = email.partition("@")
    if not separator:
        return email
    if len(local) <= 2:
        hidden_local = local[:1] + "***"
    else:
        hidden_local = local[:2] + "***" + local[-1:]
    return f"{hidden_local}@{domain}"


def password_reset_request(request):
    if request.method == "POST":
        form = PasswordResetEmailForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            otp = _generate_otp()
            expires_at = timezone.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)

            request.session["password_reset_user_id"] = user.pk
            request.session["password_reset_email"] = user.email
            request.session["password_reset_otp"] = otp
            request.session["password_reset_otp_expires_at"] = expires_at.isoformat()
            request.session["password_reset_otp_verified"] = False
            request.session["password_reset_otp_attempts"] = 0
            request.session.modified = True

            _print_password_reset_otp(user.email, otp, expires_at)
            messages.success(request, "OTP generated. Check the server terminal for the email and OTP.")
            return redirect("accounts:password_reset_verify")
    else:
        form = PasswordResetEmailForm()

    return render(request, "accounts/password_reset_form.html", {"form": form})


def password_reset_verify(request):
    user = _get_pending_reset_user(request)
    if user is None:
        messages.info(request, "Enter your email address to generate a password reset OTP.")
        return redirect("accounts:password_reset")

    if _otp_has_expired(request):
        _clear_password_reset_session(request)
        messages.error(request, "That OTP expired. Please request a new one.")
        return redirect("accounts:password_reset")

    if request.method == "POST":
        form = PasswordResetOTPForm(request.POST)
        if form.is_valid():
            otp = form.cleaned_data["otp"]
            expected_otp = request.session.get("password_reset_otp", "")
            if constant_time_compare(otp, expected_otp):
                request.session["password_reset_otp_verified"] = True
                request.session.modified = True
                messages.success(request, "OTP verified. Create your new password.")
                return redirect("accounts:password_reset_confirm")

            attempts = int(request.session.get("password_reset_otp_attempts", 0)) + 1
            request.session["password_reset_otp_attempts"] = attempts
            request.session.modified = True

            if attempts >= MAX_OTP_ATTEMPTS:
                _clear_password_reset_session(request)
                messages.error(request, "Too many incorrect OTP attempts. Please request a new OTP.")
                return redirect("accounts:password_reset")

            remaining = MAX_OTP_ATTEMPTS - attempts
            form.add_error("otp", f"Invalid OTP. {remaining} attempts remaining.")
    else:
        form = PasswordResetOTPForm()

    return render(
        request,
        "accounts/password_reset_verify.html",
        {
            "form": form,
            "email": request.session.get("password_reset_email", user.email),
            "masked_email": _masked_email(request.session.get("password_reset_email", user.email)),
            "expires_at": _get_reset_expiry(request),
        },
    )


def password_reset_confirm(request):
    user = _get_pending_reset_user(request)
    if user is None:
        messages.info(request, "Enter your email address to generate a password reset OTP.")
        return redirect("accounts:password_reset")

    if _otp_has_expired(request):
        _clear_password_reset_session(request)
        messages.error(request, "That OTP expired. Please request a new one.")
        return redirect("accounts:password_reset")

    if not request.session.get("password_reset_otp_verified"):
        messages.info(request, "Verify the OTP before choosing a new password.")
        return redirect("accounts:password_reset_verify")

    if request.method == "POST":
        form = PasswordResetNewPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            _clear_password_reset_session(request)
            messages.success(request, "Your password was updated successfully.")
            return redirect("accounts:password_reset_complete")
    else:
        form = PasswordResetNewPasswordForm(user)

    return render(request, "accounts/password_reset_confirm.html", {"form": form})


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

