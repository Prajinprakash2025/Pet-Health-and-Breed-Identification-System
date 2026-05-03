from contextlib import redirect_stdout
from io import StringIO

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


User = get_user_model()


class PasswordResetOTPTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="petowner",
            email="owner@example.com",
            password="old-password-123",
        )

    def test_password_reset_otp_flow_updates_password(self):
        output = StringIO()

        with redirect_stdout(output):
            response = self.client.post(
                reverse("accounts:password_reset"),
                {"email": self.user.email},
            )

        self.assertRedirects(response, reverse("accounts:password_reset_verify"))

        session = self.client.session
        otp = session["password_reset_otp"]
        self.assertIn(f"Email: {self.user.email}", output.getvalue())
        self.assertIn(f"OTP: {otp}", output.getvalue())

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
