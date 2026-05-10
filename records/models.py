from django.db import models
from django.conf import settings
from django.utils import timezone
from pets.models import Pet


class VaccinationRecord(models.Model):
    STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("completed", "Completed"),
        ("missed", "Missed"),
    ]

    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name="vaccinations")
    vaccine_name = models.CharField(max_length=100)
    scheduled_date = models.DateField(null=True, blank=True)
    administered_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="scheduled")
    vet_name = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-scheduled_date", "-administered_date"]

    def __str__(self) -> str:
        return f"{self.vaccine_name} for {self.pet}"


class MedicalRecord(models.Model):
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name="medical_records")
    visit_date = models.DateField()
    clinic_name = models.CharField(max_length=150, blank=True)
    diagnosis = models.TextField()
    treatment = models.TextField(blank=True)
    prescription = models.TextField(blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-visit_date"]

    def __str__(self) -> str:
        return f"Medical record for {self.pet} on {self.visit_date:%Y-%m-%d}"


class Reminder(models.Model):
    REMINDER_TYPE_CHOICES = [
        ("vaccination", "Vaccination"),
        ("grooming", "Grooming"),
        ("training", "Training"),
        ("medical", "Medical visit"),
        ("follow_up", "Follow-up"),
        ("custom", "Custom"),
    ]

    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name="reminders")
    title = models.CharField(max_length=160)
    reminder_type = models.CharField(max_length=30, choices=REMINDER_TYPE_CHOICES, default="custom")
    due_date = models.DateField()
    due_time = models.TimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    is_completed = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    push_sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["is_completed", "due_date", "due_time", "title"]

    @property
    def is_overdue(self) -> bool:
        if self.is_completed:
            return False
        today = timezone.localdate()
        if self.due_date < today:
            return True
        if self.due_date == today and self.due_time:
            return self.due_time < timezone.localtime().time()
        return False

    def __str__(self) -> str:
        due_label = self.due_date.strftime("%Y-%m-%d")
        if self.due_time:
            due_label += f" {self.due_time:%H:%M}"
        return f"{self.title} for {self.pet} on {due_label}"


class PushNotificationToken(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="push_tokens")
    token = models.TextField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"Push token for {self.user.email or self.user_id}"
