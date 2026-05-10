from datetime import timedelta
import secrets

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from django.utils.dateparse import parse_datetime
from django.utils.http import url_has_allowed_host_and_scheme

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
REGISTRATION_SESSION_KEYS = (
    "registration_verify_user_id",
    "registration_verify_email",
    "registration_verify_otp",
    "registration_verify_otp_expires_at",
    "registration_verify_otp_attempts",
)
LOGIN_SESSION_KEYS = (
    "login_verify_user_id",
    "login_verify_email",
    "login_verify_otp",
    "login_verify_otp_expires_at",
    "login_verify_otp_attempts",
    "login_verify_next",
)
OTP_EXPIRY_MINUTES = 10
MAX_OTP_ATTEMPTS = 5


class UserLoginView(LoginView):
    template_name = "accounts/login.html"
    form_class = LoginForm

    def form_valid(self, form):
        user = form.get_user()
        otp = _generate_otp()
        expires_at = timezone.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)

        try:
            _send_login_otp(user.email, otp, expires_at)
        except Exception:
            form.add_error(
                None,
                "Unable to send login OTP email. Please check the email configuration and try again.",
            )
            return self.form_invalid(form)

        self.request.session["login_verify_user_id"] = user.pk
        self.request.session["login_verify_email"] = user.email
        self.request.session["login_verify_otp"] = otp
        self.request.session["login_verify_otp_expires_at"] = expires_at.isoformat()
        self.request.session["login_verify_otp_attempts"] = 0

        next_url = self.get_redirect_url()
        if next_url:
            self.request.session["login_verify_next"] = next_url
        self.request.session.modified = True

        messages.success(self.request, "Login OTP sent to your registered email address.")
        return redirect("accounts:login_verify")


def _default_login_redirect_for_user(user):
    if user.is_staff or user.is_superuser:
        return reverse("analytics:ml_admin_dashboard")
    return reverse("home")


def logout_user(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect("home")


def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            UserProfile.objects.create(
                user=user,
                phone_number=form.cleaned_data.get("phone_number", ""),
                city=form.cleaned_data.get("city", ""),
                country=form.cleaned_data.get("country", ""),
            )

            otp = _generate_otp()
            expires_at = timezone.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)

            try:
                _send_registration_verification_otp(user.email, otp, expires_at)
            except Exception:
                user.delete()
                form.add_error(
                    None,
                    "Unable to send verification email. Please check the email configuration and try again.",
                )
                return render(request, "accounts/register.html", {"form": form})

            request.session["registration_verify_user_id"] = user.pk
            request.session["registration_verify_email"] = user.email
            request.session["registration_verify_otp"] = otp
            request.session["registration_verify_otp_expires_at"] = expires_at.isoformat()
            request.session["registration_verify_otp_attempts"] = 0
            request.session.modified = True

            messages.success(request, "Verification OTP sent to your email address.")
            return redirect("accounts:registration_verify")
    else:
        form = RegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


def _clear_registration_verification_session(request):
    for key in REGISTRATION_SESSION_KEYS:
        request.session.pop(key, None)


def _clear_login_verification_session(request):
    for key in LOGIN_SESSION_KEYS:
        request.session.pop(key, None)


def _clear_password_reset_session(request):
    for key in RESET_SESSION_KEYS:
        request.session.pop(key, None)


def _generate_otp():
    return f"{secrets.randbelow(1_000_000):06d}"


def _send_password_reset_otp(email, otp, expires_at):
    subject = "PetCare AI password reset OTP"
    message = (
        "Hello,\n\n"
        "Use the OTP below to reset your PetCare AI password.\n\n"
        f"OTP: {otp}\n"
        f"Expires at: {expires_at:%Y-%m-%d %H:%M:%S %Z}\n\n"
        "If you did not request this password reset, you can ignore this email.\n\n"
        "Regards,\n"
        "PetCare AI"
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )


def _send_registration_verification_otp(email, otp, expires_at):
    subject = "PetCare AI email verification OTP"
    message = (
        "Hello,\n\n"
        "Use the OTP below to verify your PetCare AI account.\n\n"
        f"OTP: {otp}\n"
        f"Expires at: {expires_at:%Y-%m-%d %H:%M:%S %Z}\n\n"
        "If you did not create this account, you can ignore this email.\n\n"
        "Regards,\n"
        "PetCare AI"
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )


def _send_login_otp(email, otp, expires_at):
    subject = "PetCare AI login OTP"
    message = (
        "Hello,\n\n"
        "Use the OTP below to sign in to your PetCare AI account.\n\n"
        f"OTP: {otp}\n"
        f"Expires at: {expires_at:%Y-%m-%d %H:%M:%S %Z}\n\n"
        "If you did not request this login OTP, please ignore this email.\n\n"
        "Regards,\n"
        "PetCare AI"
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )


def _get_login_expiry(request):
    value = request.session.get("login_verify_otp_expires_at")
    if not value:
        return None
    expires_at = parse_datetime(value)
    if expires_at is None:
        return None
    if timezone.is_naive(expires_at):
        expires_at = timezone.make_aware(expires_at, timezone.get_current_timezone())
    return expires_at


def _login_otp_has_expired(request):
    expires_at = _get_login_expiry(request)
    return expires_at is None or timezone.now() >= expires_at


def _get_pending_login_user(request):
    user_id = request.session.get("login_verify_user_id")
    if not user_id:
        return None
    return User.objects.filter(pk=user_id, is_active=True).first()


def login_verify(request):
    user = _get_pending_login_user(request)
    if user is None:
        messages.info(request, "Enter your email address to receive a login OTP.")
        return redirect("accounts:login")

    if _login_otp_has_expired(request):
        _clear_login_verification_session(request)
        messages.error(request, "That login OTP expired. Please request a new one.")
        return redirect("accounts:login")

    if request.method == "POST":
        form = PasswordResetOTPForm(request.POST)
        if form.is_valid():
            otp = form.cleaned_data["otp"]
            expected_otp = request.session.get("login_verify_otp", "")
            if constant_time_compare(otp, expected_otp):
                next_url = request.session.get("login_verify_next", "")
                _clear_login_verification_session(request)
                login(request, user)
                messages.success(request, "Login verified successfully.")
                if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                    return redirect(next_url)
                return redirect(_default_login_redirect_for_user(user))

            attempts = int(request.session.get("login_verify_otp_attempts", 0)) + 1
            request.session["login_verify_otp_attempts"] = attempts
            request.session.modified = True

            if attempts >= MAX_OTP_ATTEMPTS:
                _clear_login_verification_session(request)
                messages.error(request, "Too many incorrect OTP attempts. Please request a new login OTP.")
                return redirect("accounts:login")

            remaining = MAX_OTP_ATTEMPTS - attempts
            form.add_error("otp", f"Invalid OTP. {remaining} attempts remaining.")
    else:
        form = PasswordResetOTPForm()

    email = request.session.get("login_verify_email", user.email)
    return render(
        request,
        "accounts/login_verify.html",
        {
            "form": form,
            "email": email,
            "masked_email": _masked_email(email),
            "expires_at": _get_login_expiry(request),
        },
    )


def _get_registration_expiry(request):
    value = request.session.get("registration_verify_otp_expires_at")
    if not value:
        return None
    expires_at = parse_datetime(value)
    if expires_at is None:
        return None
    if timezone.is_naive(expires_at):
        expires_at = timezone.make_aware(expires_at, timezone.get_current_timezone())
    return expires_at


def _registration_otp_has_expired(request):
    expires_at = _get_registration_expiry(request)
    return expires_at is None or timezone.now() >= expires_at


def _get_pending_registration_user(request):
    user_id = request.session.get("registration_verify_user_id")
    if not user_id:
        return None
    return User.objects.filter(pk=user_id, is_active=False).first()


def registration_verify(request):
    user = _get_pending_registration_user(request)
    if user is None:
        messages.info(request, "Create an account to receive a verification OTP.")
        return redirect("accounts:register")

    if _registration_otp_has_expired(request):
        user.delete()
        _clear_registration_verification_session(request)
        messages.error(request, "That verification OTP expired. Please register again.")
        return redirect("accounts:register")

    if request.method == "POST":
        form = PasswordResetOTPForm(request.POST)
        if form.is_valid():
            otp = form.cleaned_data["otp"]
            expected_otp = request.session.get("registration_verify_otp", "")
            if constant_time_compare(otp, expected_otp):
                user.is_active = True
                user.save(update_fields=["is_active"])
                _clear_registration_verification_session(request)
                login(request, user)
                messages.success(request, "Email verified successfully. Your account is ready.")
                return redirect("home")

            attempts = int(request.session.get("registration_verify_otp_attempts", 0)) + 1
            request.session["registration_verify_otp_attempts"] = attempts
            request.session.modified = True

            if attempts >= MAX_OTP_ATTEMPTS:
                user.delete()
                _clear_registration_verification_session(request)
                messages.error(request, "Too many incorrect OTP attempts. Please register again.")
                return redirect("accounts:register")

            remaining = MAX_OTP_ATTEMPTS - attempts
            form.add_error("otp", f"Invalid OTP. {remaining} attempts remaining.")
    else:
        form = PasswordResetOTPForm()

    email = request.session.get("registration_verify_email", user.email)
    return render(
        request,
        "accounts/registration_verify.html",
        {
            "form": form,
            "email": email,
            "masked_email": _masked_email(email),
            "expires_at": _get_registration_expiry(request),
        },
    )


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

            try:
                _send_password_reset_otp(user.email, otp, expires_at)
            except Exception:
                form.add_error(
                    None,
                    "Unable to send OTP email. Please check the email configuration and try again.",
                )
                return render(request, "accounts/password_reset_form.html", {"form": form})

            request.session["password_reset_user_id"] = user.pk
            request.session["password_reset_email"] = user.email
            request.session["password_reset_otp"] = otp
            request.session["password_reset_otp_expires_at"] = expires_at.isoformat()
            request.session["password_reset_otp_verified"] = False
            request.session["password_reset_otp_attempts"] = 0
            request.session.modified = True

            messages.success(request, "OTP sent to your registered email address.")
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

