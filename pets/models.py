from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class Pet(models.Model):
    SPECIES_CHOICES = [
        ("dog", "Dog"),
        ("cat", "Cat"),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="pets")
    name = models.CharField(max_length=100)
    species = models.CharField(max_length=20, choices=SPECIES_CHOICES)
    breed = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    image = models.ImageField(upload_to="pet_images/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.name} ({self.species})"


class BreedPrediction(models.Model):
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name="breed_predictions")
    predicted_breed = models.CharField(max_length=100)
    species = models.CharField(max_length=20)
    confidence = models.DecimalField(max_digits=5, decimal_places=2, help_text="Confidence percentage (0-100).")
    model_version = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.pet} -> {self.predicted_breed} ({self.confidence}%)"


class HealthAssessment(models.Model):
    RISK_LEVEL_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]

    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name="health_assessments")
    assessment_date = models.DateTimeField(auto_now_add=True)

    skin_infection_risk = models.CharField(max_length=10, choices=RISK_LEVEL_CHOICES, default="low")
    fur_loss_risk = models.CharField(max_length=10, choices=RISK_LEVEL_CHOICES, default="low")
    eye_issue_risk = models.CharField(max_length=10, choices=RISK_LEVEL_CHOICES, default="low")
    wound_risk = models.CharField(max_length=10, choices=RISK_LEVEL_CHOICES, default="low")
    parasite_risk = models.CharField(max_length=10, choices=RISK_LEVEL_CHOICES, default="low")
    obesity_risk = models.CharField(max_length=10, choices=RISK_LEVEL_CHOICES, default="low")

    overall_risk_level = models.CharField(max_length=10, choices=RISK_LEVEL_CHOICES, default="low")
    notes = models.TextField(blank=True)
    scan_image = models.ImageField(upload_to="health_scans/", null=True, blank=True)
    symptom_details = models.TextField(blank=True, help_text="Optional symptom details provided by user.")
    care_recommendations = models.TextField(blank=True, help_text="AI generated care recommendations.")

    class Meta:
        ordering = ["-assessment_date"]

    def __str__(self) -> str:
        return f"Health assessment for {self.pet} on {self.assessment_date:%Y-%m-%d}"
