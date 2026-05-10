from datetime import timedelta

from django.db.models import Q
from django.utils import timezone


def due_reminder_filter(days_ahead=0):
    today = timezone.localdate()
    current_time = timezone.localtime().time()
    target_date = today + timedelta(days=max(days_ahead, 0))

    if target_date > today:
        return Q(due_date__lte=target_date)

    return (
        Q(due_date__lt=today)
        | Q(due_date=today, due_time__isnull=True)
        | Q(due_date=today, due_time__lte=current_time)
    )
