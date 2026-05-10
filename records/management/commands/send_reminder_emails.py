from django.core.management.base import BaseCommand

from records.email_utils import get_pending_email_reminders, send_reminder_email


class Command(BaseCommand):
    help = "Send reminder emails for incomplete reminders that are due or overdue."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days-ahead",
            type=int,
            default=0,
            help="Also include reminders due within this many days from today.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show which reminders would be emailed without sending emails.",
        )

    def handle(self, *args, **options):
        days_ahead = max(options["days_ahead"], 0)
        dry_run = options["dry_run"]
        reminders = list(get_pending_email_reminders(days_ahead=days_ahead))

        sent_count = 0
        skipped_count = 0
        failed_count = 0

        if not reminders:
            self.stdout.write(self.style.SUCCESS("No reminder emails to send."))
            return

        for reminder in reminders:
            label = f"{reminder.title} for {reminder.pet.name} ({reminder.due_date:%Y-%m-%d})"
            try:
                sent, reason = send_reminder_email(reminder, dry_run=dry_run)
            except Exception as exc:
                failed_count += 1
                self.stderr.write(self.style.ERROR(f"Failed: {label} - {exc}"))
                continue

            if sent:
                sent_count += 1
                action = "Would send" if dry_run else "Sent"
                self.stdout.write(self.style.SUCCESS(f"{action}: {label}"))
            else:
                skipped_count += 1
                self.stdout.write(self.style.WARNING(f"Skipped: {label} - {reason}"))

        summary_action = "would be sent" if dry_run else "sent"
        self.stdout.write(
            self.style.SUCCESS(
                f"Reminder email summary: {sent_count} {summary_action}, "
                f"{skipped_count} skipped, {failed_count} failed."
            )
        )
