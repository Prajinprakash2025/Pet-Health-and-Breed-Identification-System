from django.contrib import admin

from .models import MedicalRecord, Reminder, VaccinationRecord


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
    list_display = ("title", "pet", "reminder_type", "due_date", "is_completed")
    list_filter = ("reminder_type", "due_date", "is_completed")
    search_fields = ("title", "pet__name", "notes")
