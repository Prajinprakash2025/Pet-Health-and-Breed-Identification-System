from django.db import models


class BreedInfo(models.Model):
    SPECIES_CHOICES = [
        ("dog", "Dog"),
        ("cat", "Cat"),
    ]

    species = models.CharField(max_length=20, choices=SPECIES_CHOICES)
    breed_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    typical_weight_min_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    typical_weight_max_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    temperament = models.CharField(max_length=255, blank=True)
    grooming_needs = models.TextField(blank=True)
    exercise_needs = models.TextField(blank=True)

    class Meta:
        unique_together = ("species", "breed_name")
        verbose_name = "Breed information"
        verbose_name_plural = "Breed information"

    def __str__(self) -> str:
        return f"{self.breed_name} ({self.species})"


class DiseaseInfo(models.Model):
    SPECIES_CHOICES = [
        ("dog", "Dog"),
        ("cat", "Cat"),
    ]

    species = models.CharField(max_length=20, choices=SPECIES_CHOICES)
    name = models.CharField(max_length=150)
    common_symptoms = models.TextField()
    prevention = models.TextField(blank=True)
    treatment = models.TextField(blank=True)

    class Meta:
        unique_together = ("species", "name")

    def __str__(self) -> str:
        return f"{self.name} ({self.species})"


class VaccinationScheduleTemplate(models.Model):
    SPECIES_CHOICES = [
        ("dog", "Dog"),
        ("cat", "Cat"),
    ]

    species = models.CharField(max_length=20, choices=SPECIES_CHOICES)
    vaccine_name = models.CharField(max_length=100)
    recommended_age_weeks = models.PositiveIntegerField(help_text="Recommended age in weeks for first dose.")
    repeat_interval_weeks = models.PositiveIntegerField(null=True, blank=True, help_text="Interval for booster doses, if applicable.")
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ("species", "vaccine_name", "recommended_age_weeks")
        verbose_name = "Vaccination schedule template"

    def __str__(self) -> str:
        return f"{self.vaccine_name} ({self.species})"
