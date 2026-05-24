from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse


User = get_user_model()


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="PetCare Test <test@example.com>",
)
class PasswordResetOTPTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="petowner",
            email="owner@example.com",
            password="old-password-123",
        )

    def test_password_reset_otp_flow_updates_password(self):
        response = self.client.post(
            reverse("accounts:password_reset"),
            {"email": self.user.email},
        )

        self.assertRedirects(response, reverse("accounts:password_reset_verify"))

        session = self.client.session
        otp = session["password_reset_otp"]
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])
        self.assertIn("PetCare AI password reset OTP", mail.outbox[0].subject)
        self.assertIn(f"OTP: {otp}", mail.outbox[0].body)

        invalid_otp = "000000" if otp != "000000" else "111111"
        response = self.client.post(
            reverse("accounts:password_reset_verify"),
            {"otp": invalid_otp},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid OTP")

        response = self.client.post(
            reverse("accounts:password_reset_verify"),
            {"otp": otp},
        )
        self.assertRedirects(response, reverse("accounts:password_reset_confirm"))

        new_password = "A-strong-pass-2026"
        response = self.client.post(
            reverse("accounts:password_reset_confirm"),
            {
                "new_password1": new_password,
                "new_password2": new_password,
            },
        )
        self.assertRedirects(response, reverse("accounts:password_reset_complete"))

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(new_password))
        self.assertNotIn("password_reset_otp", self.client.session)


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="PetCare Test <test@example.com>",
)
class EmailAuthenticationTests(TestCase):
    def test_registration_uses_email_without_username_field(self):
        response = self.client.get(reverse("accounts:register"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'name="username"')
        self.assertNotContains(response, 'name="password1"')
        self.assertNotContains(response, 'name="password2"')
        self.assertContains(response, 'name="email"')

        response = self.client.post(
            reverse("accounts:register"),
            {
                "email": "newowner@example.com",
                "first_name": "New",
                "last_name": "Owner",
            },
        )
        self.assertRedirects(response, reverse("accounts:registration_verify"))

        user = User.objects.get(email="newowner@example.com")
        self.assertEqual(user.first_name, "New")
        self.assertTrue(user.username)
        self.assertNotEqual(user.username, "")
        self.assertFalse(user.has_usable_password())
        self.assertFalse(user.is_active)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["newowner@example.com"])

        otp = self.client.session["registration_verify_otp"]
        self.assertIn("PetCare AI email verification OTP", mail.outbox[0].subject)
        self.assertIn(f"OTP: {otp}", mail.outbox[0].body)

        response = self.client.post(
            reverse("accounts:registration_verify"),
            {"otp": otp},
        )
        self.assertRedirects(response, reverse("home"))

        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_login_uses_email_otp_without_password(self):
        response = self.client.get(reverse("accounts:login"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'name="username"')
        self.assertNotContains(response, 'name="password"')
        self.assertContains(response, 'name="email"')

        user = User.objects.create_user(
            username="hidden-internal-name",
            email="owner@example.com",
            password="Strong-pass-2026",
        )

        response = self.client.post(
            reverse("accounts:login"),
            {
                "email": "owner@example.com",
            },
        )
        self.assertRedirects(response, reverse("accounts:login_verify"))
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("PetCare AI login OTP", mail.outbox[0].subject)

        otp = self.client.session["login_verify_otp"]
        self.assertIn(f"OTP: {otp}", mail.outbox[0].body)

        response = self.client.post(
            reverse("accounts:login_verify"),
            {"otp": otp},
        )
        self.assertRedirects(response, reverse("home"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)


class ProfileEditTests(TestCase):
    def test_profile_edit_updates_display_name(self):
        user = User.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="Strong-pass-2026",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("accounts:profile_edit"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="first_name"')
        self.assertContains(response, 'name="last_name"')

        response = self.client.post(
            reverse("accounts:profile_edit"),
            {
                "first_name": "Akhil",
                "last_name": "Santhosh",
                "phone_number": "9876543210",
                "address": "Home",
                "city": "Kochi",
                "country": "India",
            },
        )
        self.assertRedirects(response, reverse("accounts:profile"))

        user.refresh_from_db()
        self.assertEqual(user.get_full_name(), "Akhil Santhosh")
        self.assertContains(self.client.get(reverse("accounts:profile")), "Akhil Santhosh")
