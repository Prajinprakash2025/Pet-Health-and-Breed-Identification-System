from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import Reminder
from .schedule_utils import due_reminder_filter


def get_pending_email_reminders(days_ahead=0):
    return (
        Reminder.objects.filter(
            due_reminder_filter(days_ahead=days_ahead),
            is_completed=False,
            email_sent_at__isnull=True,
        )
        .select_related("pet", "pet__owner")
        .order_by("due_date", "due_time", "pet__name", "title")
    )


def build_reminder_email(reminder):
    pet = reminder.pet
    owner = pet.owner
    display_name = owner.get_full_name() or owner.email or owner.username
    due_label = reminder.due_date.strftime("%d %b %Y")
    if reminder.due_time:
        due_label += reminder.due_time.strftime(" at %I:%M %p")
    reminder_type = reminder.get_reminder_type_display()

    subject = f"PetCare Reminder: {reminder.title} for {pet.name}"
    message = (
        f"Hello {display_name},\n\n"
        f"This is a reminder for your pet {pet.name}.\n\n"
        f"Reminder: {reminder.title}\n"
        f"Type: {reminder_type}\n"
        f"Due date: {due_label}\n"
    )
    if reminder.notes:
        message += f"Notes: {reminder.notes}\n"
    message += (
        "\nPlease log in to PetCare AI to update or complete this reminder.\n\n"
        "Regards,\n"
        "PetCare AI"
    )
    return subject, message


def send_reminder_email(reminder, dry_run=False):
    owner_email = reminder.pet.owner.email
    if not owner_email:
        return False, "missing owner email"

    subject, message = build_reminder_email(reminder)
    if dry_run:
        return True, "dry run"

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[owner_email],
        fail_silently=False,
    )
    reminder.email_sent_at = timezone.now()
    reminder.save(update_fields=["email_sent_at"])
    return True, "sent"
