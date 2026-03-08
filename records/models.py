from django.db import models
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
