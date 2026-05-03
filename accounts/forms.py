from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import SetPasswordForm, UserCreationForm
from django.utils.text import slugify

from .models import UserProfile


User = get_user_model()


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "email",
                "placeholder": "you@example.com",
            }
        ),
    )
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    phone_number = forms.CharField(max_length=20, required=False)
    city = forms.CharField(max_length=100, required=False)
    country = forms.CharField(max_length=100, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("email", "first_name", "last_name")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists. Please sign in instead.")
        return email

    def _generate_username(self, email: str) -> str:
        max_length = User._meta.get_field(User.USERNAME_FIELD).max_length
        base = slugify(email.split("@", 1)[0]) or "user"
        base = base[:max_length]
        username = base
        counter = 1

        while User.objects.filter(username__iexact=username).exists():
            suffix = f"-{counter}"
            username = f"{base[:max_length - len(suffix)]}{suffix}"
            counter += 1
        return username

    def save(self, commit: bool = True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.username = self._generate_username(user.email)
        user.first_name = self.cleaned_data.get("first_name", "")
        user.last_name = self.cleaned_data.get("last_name", "")

        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                phone_number=self.cleaned_data.get("phone_number", ""),
                city=self.cleaned_data.get("city", ""),
                country=self.cleaned_data.get("country", ""),
            )
        return user


class LoginForm(forms.Form):
    error_messages = {
        "invalid_login": "Please enter a correct email address and password.",
        "inactive": "This account is inactive.",
    }

    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "autofocus": True,
                "autocomplete": "email",
                "class": "form-control",
                "placeholder": "you@example.com",
            }
        ),
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "current-password",
                "class": "form-control",
            }
        ),
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        email = self.cleaned_data.get("email")
        password = self.cleaned_data.get("password")

        if email is not None and password:
            email = email.strip().lower()
            user = User.objects.filter(email__iexact=email).first()
            if user is None:
                raise self.get_invalid_login_error()

            self.user_cache = authenticate(
                self.request,
                username=user.get_username(),
                password=password,
            )
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            self.confirm_login_allowed(self.user_cache)
            self.cleaned_data["email"] = email

        return self.cleaned_data

    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise forms.ValidationError(
                self.error_messages["inactive"],
                code="inactive",
            )

    def get_invalid_login_error(self):
        return forms.ValidationError(
            self.error_messages["invalid_login"],
            code="invalid_login",
        )

    def get_user(self):
        return self.user_cache


class PasswordResetEmailForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "autocomplete": "email",
                "placeholder": "you@example.com",
            }
        ),
    )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if user is None:
            raise forms.ValidationError("No active account was found with this email address.")
        self.user = user
        return email

    def get_user(self):
        return getattr(self, "user", None)


class PasswordResetOTPForm(forms.Form):
    otp = forms.CharField(
        label="OTP",
        min_length=6,
        max_length=6,
        widget=forms.TextInput(
            attrs={
                "class": "form-control otp-input",
                "autocomplete": "one-time-code",
                "inputmode": "numeric",
                "pattern": "[0-9]*",
                "placeholder": "000000",
            }
        ),
    )

    def clean_otp(self):
        otp = self.cleaned_data["otp"].strip()
        if not otp.isdigit():
            raise forms.ValidationError("Enter the 6-digit OTP from the terminal.")
        return otp


class PasswordResetNewPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ("phone_number", "address", "city", "country")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})


