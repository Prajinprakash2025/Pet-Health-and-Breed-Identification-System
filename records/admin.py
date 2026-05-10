from django.contrib import admin

from .models import MedicalRecord, PushNotificationToken, Reminder, VaccinationRecord


@admin.register(VaccinationRecord)
class VaccinationRecordAdmin(admin.ModelAdmin):
    list_display = ("pet", "vaccine_name", "scheduled_date", "administered_date", "status")
    list_filter = ("status", "scheduled_date", "administered_date")
    search_fields = ("pet__name", "vaccine_name", "vet_name", "notes")


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ("pet", "visit_date", "clinic_name", "follow_up_date")
    list_filter = ("visit_date", "follow_up_date", "clinic_name")
    search_fields = ("pet__name", "clinic_name", "diagnosis", "treatment", "prescription")


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "pet",
        "reminder_type",
        "due_date",
        "due_time",
        "is_completed",
        "email_sent_at",
        "push_sent_at",
    )
    list_filter = ("reminder_type", "due_date", "due_time", "is_completed", "email_sent_at", "push_sent_at")
    search_fields = ("title", "pet__name", "notes")


@admin.register(PushNotificationToken)
class PushNotificationTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "is_active", "created_at", "updated_at")
    list_filter = ("is_active", "created_at", "updated_at")
    search_fields = ("user__email", "user__username", "token")
