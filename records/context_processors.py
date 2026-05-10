import json

from django.conf import settings


def reminder_notifications(request):
    firebase_web_config_available = (
        request.user.is_authenticated
        and settings.FIREBASE_WEB_API_KEY
        and settings.FIREBASE_PROJECT_ID
        and settings.FIREBASE_MESSAGING_SENDER_ID
        and settings.FIREBASE_APP_ID
    )
    firebase_config = {
        "apiKey": settings.FIREBASE_WEB_API_KEY,
        "authDomain": settings.FIREBASE_AUTH_DOMAIN,
        "projectId": settings.FIREBASE_PROJECT_ID,
        "storageBucket": settings.FIREBASE_STORAGE_BUCKET,
        "messagingSenderId": settings.FIREBASE_MESSAGING_SENDER_ID,
        "appId": settings.FIREBASE_APP_ID,
        "measurementId": settings.FIREBASE_MEASUREMENT_ID,
    }

    return {
        "firebase_web_config_available": firebase_web_config_available,
        "firebase_messaging_enabled": firebase_web_config_available and settings.FIREBASE_VAPID_KEY_LOOKS_VALID,
        "firebase_vapid_key_looks_valid": settings.FIREBASE_VAPID_KEY_LOOKS_VALID,
        "firebase_config_json": json.dumps(firebase_config),
        "firebase_vapid_key": settings.FIREBASE_VAPID_KEY,
    }
