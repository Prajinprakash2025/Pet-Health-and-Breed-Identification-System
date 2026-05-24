from .models import MissingPetNotification


def user_notifications(request):
    if not request.user.is_authenticated:
        return {
            "nav_notifications": [],
            "nav_unread_notifications_count": 0,
        }

    notifications = MissingPetNotification.objects.filter(user=request.user)
    return {
        "nav_notifications": notifications[:5],
        "nav_unread_notifications_count": notifications.filter(is_read=False).count(),
    }
