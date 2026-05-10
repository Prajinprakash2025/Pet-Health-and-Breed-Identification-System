import logging
import os
import sys
import threading
import time

from django.conf import settings
from django.db import close_old_connections

logger = logging.getLogger(__name__)

_started = False


def _is_runserver_process():
    if "runserver" not in sys.argv:
        return False
    if settings.DEBUG and os.environ.get("RUN_MAIN") != "true":
        return False
    return True


def _can_start_reminder_worker():
    return (
        settings.AUTO_SEND_REMINDER_PUSH
        and settings.FIREBASE_MESSAGING_ENABLED
        and bool(settings.FIREBASE_SERVICE_ACCOUNT_FILE)
        and _is_runserver_process()
    )


def start_reminder_push_worker():
    global _started
    if _started or not _can_start_reminder_worker():
        return

    _started = True
    interval = max(settings.REMINDER_PUSH_INTERVAL_SECONDS, 30)
    thread = threading.Thread(
        target=_reminder_push_loop,
        args=(interval,),
        name="reminder-push-worker",
        daemon=True,
    )
    thread.start()
    logger.info("Reminder push worker started with %s second interval.", interval)


def _reminder_push_loop(interval):
    from .push_utils import get_pending_push_reminders, send_reminder_push

    while True:
        try:
            close_old_connections()
            for reminder in get_pending_push_reminders(days_ahead=0):
                sent, reason = send_reminder_push(reminder)
                if sent:
                    logger.info("Reminder push sent for reminder %s: %s", reminder.id, reason)
                else:
                    logger.info("Reminder push skipped for reminder %s: %s", reminder.id, reason)
        except Exception:
            logger.exception("Reminder push worker failed.")
        finally:
            close_old_connections()
            time.sleep(interval)
