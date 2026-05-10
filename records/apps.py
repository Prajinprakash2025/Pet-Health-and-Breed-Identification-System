from django.apps import AppConfig


class RecordsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'records'

    def ready(self):
        from .background_tasks import start_reminder_push_worker

        start_reminder_push_worker()
