import json
from io import StringIO
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from pets.models import Pet

from .models import PushNotificationToken, Reminder
from .push_utils import send_user_push


User = get_user_model()


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="PetCare Test <test@example.com>",
)
class ReminderEmailCommandTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="Strong-pass-2026",
        )
        self.pet = Pet.objects.create(
            owner=self.user,
            name="Milo",
            species="dog",
        )

    def create_reminder(self, title, due_date, **kwargs):
        return Reminder.objects.create(
            pet=kwargs.pop("pet", self.pet),
            title=title,
            reminder_type=kwargs.pop("reminder_type", "custom"),
            due_date=due_date,
            notes=kwargs.pop("notes", ""),
            **kwargs,
        )

    def test_sends_due_and_overdue_reminders_once(self):
        today = timezone.localdate()
        due_today = self.create_reminder("Bath day", today)
        overdue = self.create_reminder("Vet visit", today - timedelta(days=1))
        future = self.create_reminder("Training", today + timedelta(days=1))
        completed = self.create_reminder("Completed task", today, is_completed=True)
        already_sent = self.create_reminder("Already sent", today, email_sent_at=timezone.now())

        no_email_user = User.objects.create_user(
            username="no-email",
            email="",
            password="Strong-pass-2026",
        )
        no_email_pet = Pet.objects.create(owner=no_email_user, name="NoMail", species="cat")
        no_email = self.create_reminder("No email reminder", today, pet=no_email_pet)

        out = StringIO()
        call_command("send_reminder_emails", stdout=out)

        self.assertEqual(len(mail.outbox), 2)
        subjects = {message.subject for message in mail.outbox}
        self.assertIn("PetCare Reminder: Bath day for Milo", subjects)
        self.assertIn("PetCare Reminder: Vet visit for Milo", subjects)

        due_today.refresh_from_db()
        overdue.refresh_from_db()
        future.refresh_from_db()
        completed.refresh_from_db()
        already_sent.refresh_from_db()
        no_email.refresh_from_db()

        self.assertIsNotNone(due_today.email_sent_at)
        self.assertIsNotNone(overdue.email_sent_at)
        self.assertIsNone(future.email_sent_at)
        self.assertIsNone(completed.email_sent_at)
        self.assertIsNotNone(already_sent.email_sent_at)
        self.assertIsNone(no_email.email_sent_at)
        self.assertIn("2 sent", out.getvalue())
        self.assertIn("1 skipped", out.getvalue())

        call_command("send_reminder_emails", stdout=StringIO())
        self.assertEqual(len(mail.outbox), 2)

    def test_days_ahead_sends_upcoming_reminders(self):
        tomorrow = timezone.localdate() + timedelta(days=1)
        reminder = self.create_reminder("Tomorrow vaccine", tomorrow)

        call_command("send_reminder_emails", "--days-ahead=1", stdout=StringIO())

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Tomorrow vaccine", mail.outbox[0].subject)
        reminder.refresh_from_db()
        self.assertIsNotNone(reminder.email_sent_at)

    def test_dry_run_does_not_send_or_mark_reminder(self):
        reminder = self.create_reminder("Dry run reminder", timezone.localdate())
        out = StringIO()

        call_command("send_reminder_emails", "--dry-run", stdout=out)

        self.assertEqual(len(mail.outbox), 0)
        reminder.refresh_from_db()
        self.assertIsNone(reminder.email_sent_at)
        self.assertIn("Would send", out.getvalue())


class ReminderPushNotificationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="notify-owner",
            email="notify@example.com",
            password="Strong-pass-2026",
        )
        self.pet = Pet.objects.create(owner=self.user, name="Bella", species="cat")

    def test_authenticated_user_can_save_push_token(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("records:save_push_token"),
            data=json.dumps({"token": "test-fcm-token"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        token = PushNotificationToken.objects.get(token="test-fcm-token")
        self.assertEqual(token.user, self.user)
        self.assertTrue(token.is_active)

    def test_push_command_dry_run_does_not_mark_reminder(self):
        reminder = Reminder.objects.create(
            pet=self.pet,
            title="Due medicine",
            reminder_type="medical",
            due_date=timezone.localdate(),
        )
        PushNotificationToken.objects.create(user=self.user, token="test-fcm-token")
        out = StringIO()

        call_command("send_reminder_push_notifications", "--dry-run", stdout=out)

        reminder.refresh_from_db()
        self.assertIsNone(reminder.push_sent_at)
        self.assertIn("Would send", out.getvalue())

    def test_push_command_waits_until_due_time(self):
        now = timezone.localtime()
        past_time = (now - timedelta(minutes=5)).time().replace(second=0, microsecond=0)
        future_time = (now + timedelta(minutes=30)).time().replace(second=0, microsecond=0)
        due_now = Reminder.objects.create(
            pet=self.pet,
            title="Medicine now",
            reminder_type="medical",
            due_date=timezone.localdate(),
            due_time=past_time,
        )
        later = Reminder.objects.create(
            pet=self.pet,
            title="Medicine later",
            reminder_type="medical",
            due_date=timezone.localdate(),
            due_time=future_time,
        )
        PushNotificationToken.objects.create(user=self.user, token="test-fcm-token")
        out = StringIO()

        call_command("send_reminder_push_notifications", "--dry-run", stdout=out)

        output = out.getvalue()
        self.assertIn(due_now.title, output)
        self.assertNotIn(later.title, output)

    def test_send_user_push_uses_firebase_token_and_url(self):
        class FakeMessaging:
            sent_messages = []

            class Notification:
                def __init__(self, title, body):
                    self.title = title
                    self.body = body

            class Message:
                def __init__(self, notification, data, token):
                    self.notification = notification
                    self.data = data
                    self.token = token

            @classmethod
            def send(cls, message):
                cls.sent_messages.append(message)

        PushNotificationToken.objects.create(user=self.user, token="test-fcm-token")

        with patch("records.push_utils._get_firebase_messaging", return_value=FakeMessaging):
            sent, reason = send_user_push(
                self.user,
                "New sighting for Milo",
                "Someone reported seeing Milo near City Park.",
                "http://127.0.0.1:8000/pets/missing/1/",
            )

        self.assertTrue(sent)
        self.assertEqual(reason, "sent to 1 device(s)")
        self.assertEqual(len(FakeMessaging.sent_messages), 1)
        message = FakeMessaging.sent_messages[0]
        self.assertEqual(message.notification.title, "New sighting for Milo")
        self.assertEqual(message.notification.body, "Someone reported seeing Milo near City Park.")
        self.assertEqual(message.data["url"], "http://127.0.0.1:8000/pets/missing/1/")
        self.assertEqual(message.token, "test-fcm-token")
