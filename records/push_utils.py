from urllib.parse import urljoin

from django.conf import settings
from django.utils import timezone

from .models import PushNotificationToken, Reminder
from .schedule_utils import due_reminder_filter


def get_pending_push_reminders(days_ahead=0):
    return (
        Reminder.objects.filter(
            due_reminder_filter(days_ahead=days_ahead),
            is_completed=False,
            push_sent_at__isnull=True,
        )
        .select_related("pet", "pet__owner")
        .order_by("due_date", "due_time", "pet__name", "title")
    )


def _get_firebase_messaging():
    try:
        import firebase_admin
        from firebase_admin import credentials, messaging
    except ImportError as exc:
        raise RuntimeError(
            "firebase-admin is not installed. Run: pip install firebase-admin"
        ) from exc

    try:
        firebase_admin.get_app()
    except ValueError:
        if settings.FIREBASE_SERVICE_ACCOUNT_FILE:
            credential = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_FILE)
            firebase_admin.initialize_app(credential)
        else:
            firebase_admin.initialize_app()

    return messaging


def _should_deactivate_token(exc):
    return exc.__class__.__name__ in {
        "UnregisteredError",
        "RegistrationTokenNotRegisteredError",
    }


def build_reminder_push(reminder):
    pet = reminder.pet
    due_label = reminder.due_date.strftime("%d %b %Y")
    if reminder.due_time:
        due_label += reminder.due_time.strftime(" at %I:%M %p")
    title = f"PetCare Reminder: {reminder.title}"
    body = f"{pet.name} has a {reminder.get_reminder_type_display()} reminder due on {due_label}."
    reminder_url = urljoin(f"{settings.SITE_URL}/", "records/reminders/")
    return title, body, reminder_url


def send_reminder_push(reminder, dry_run=False):
    tokens = list(
        PushNotificationToken.objects.filter(
            user=reminder.pet.owner,
            is_active=True,
        )
    )
    if not tokens:
        return False, "missing push token"

    if dry_run:
        return True, f"dry run for {len(tokens)} device(s)"

    messaging = _get_firebase_messaging()
    title, body, reminder_url = build_reminder_push(reminder)

    sent_count = 0
    inactive_count = 0
    failures = []
    for token in tokens:
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data={"url": reminder_url},
            token=token.token,
        )
        try:
            messaging.send(message)
        except Exception as exc:
            if _should_deactivate_token(exc):
                token.is_active = False
                token.save(update_fields=["is_active", "updated_at"])
                inactive_count += 1
                continue
            failures.append(str(exc))
            continue
        sent_count += 1

    if sent_count:
        reminder.push_sent_at = timezone.now()
        reminder.save(update_fields=["push_sent_at"])
        details = f"sent to {sent_count} device(s)"
        if inactive_count:
            details += f", deactivated {inactive_count} expired token(s)"
        return True, details

    if failures:
        return False, "; ".join(failures[:2])
    return False, "all push tokens are inactive"


def send_user_push(user, title, body, url, dry_run=False):
    tokens = list(PushNotificationToken.objects.filter(user=user, is_active=True))
    if not tokens:
        return False, "missing push token"

    if dry_run:
        return True, f"dry run for {len(tokens)} device(s)"

    messaging = _get_firebase_messaging()
    sent_count = 0
    inactive_count = 0
    failures = []

    for token in tokens:
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data={"url": url},
            token=token.token,
        )
        try:
            messaging.send(message)
        except Exception as exc:
            if _should_deactivate_token(exc):
                token.is_active = False
                token.save(update_fields=["is_active", "updated_at"])
                inactive_count += 1
                continue
            failures.append(str(exc))
            continue
        sent_count += 1

    if sent_count:
        details = f"sent to {sent_count} device(s)"
        if inactive_count:
            details += f", deactivated {inactive_count} expired token(s)"
        return True, details

    if failures:
        return False, "; ".join(failures[:2])
    return False, "all push tokens are inactive"
