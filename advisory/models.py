from django.db import models
from django.conf import settings


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


class CareAdvisory(models.Model):
    SPECIES_CHOICES = [
        ("dog", "Dog"),
        ("cat", "Cat"),
        ("both", "Dog & Cat"),
    ]
    CATEGORY_CHOICES = [
        ("vaccination", "Vaccination schedule"),
        ("diet", "Diet & nutrition"),
        ("grooming", "Grooming practices"),
        ("hygiene", "Hygiene care"),
        ("parasite", "Parasite prevention"),
        ("treatment", "Treatment suggestions"),
    ]

    species = models.CharField(max_length=20, choices=SPECIES_CHOICES, default="both")
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    title = models.CharField(max_length=160)
    short_summary = models.CharField(max_length=255, blank=True)
    recommendation = models.TextField()
    when_to_apply = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category", "species", "title"]
        verbose_name = "Care advisory"
        verbose_name_plural = "Care advisories"

    def __str__(self) -> str:
        return f"{self.title} ({self.get_category_display()})"


class MedicineRecommendation(models.Model):
    SPECIES_CHOICES = CareAdvisory.SPECIES_CHOICES

    species = models.CharField(max_length=20, choices=SPECIES_CHOICES, default="both")
    condition_name = models.CharField(max_length=150)
    medicine_name = models.CharField(max_length=150)
    dosage_guidance = models.TextField(
        help_text="Use vet-safe guidance only. Avoid exact dosage unless prescribed."
    )
    administration_notes = models.TextField(blank=True)
    warnings = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["species", "condition_name", "medicine_name"]
        unique_together = ("species", "condition_name", "medicine_name")

    def __str__(self) -> str:
        return f"{self.medicine_name} for {self.condition_name}"


class PetService(models.Model):
    SERVICE_TYPE_CHOICES = [
        ("vet", "Veterinary clinic"),
        ("groomer", "Groomer"),
        ("trainer", "Trainer"),
        ("boarding", "Boarding"),
        ("pharmacy", "Pet pharmacy"),
    ]

    name = models.CharField(max_length=180)
    service_type = models.CharField(max_length=30, choices=SERVICE_TYPE_CHOICES)
    city = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    opening_hours = models.CharField(max_length=160, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["city", "service_type", "name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.get_service_type_display()})"


class VetDoctor(models.Model):
    SPECIALIZATION_CHOICES = [
        ("general", "General Practice"),
        ("surgery", "Surgery"),
        ("dermatology", "Dermatology"),
        ("cardiology", "Cardiology"),
        ("dentistry", "Dentistry"),
        ("orthopedics", "Orthopedics"),
        ("neurology", "Neurology"),
        ("oncology", "Oncology"),
        ("ophthalmology", "Ophthalmology"),
        ("emergency", "Emergency & Critical Care"),
    ]

    name = models.CharField(max_length=150)
    specialization = models.CharField(max_length=50, choices=SPECIALIZATION_CHOICES, default="general")
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    clinic_name = models.CharField(max_length=200, blank=True)
    address = models.TextField(blank=True)
    photo = models.ImageField(upload_to="doctor_photos/", null=True, blank=True)
    experience_years = models.PositiveIntegerField(default=0, help_text="Years of experience.")
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Dr. {self.name} ({self.get_specialization_display()})"


class ServiceBooking(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("cancelled", "Cancelled"),
        ("completed", "Completed"),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    pet_service = models.ForeignKey(PetService, on_delete=models.SET_NULL, null=True, blank=True)
    vet_doctor = models.ForeignKey(VetDoctor, on_delete=models.SET_NULL, null=True, blank=True)
    booking_date = models.DateField()
    booking_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-booking_date", "-booking_time"]

    def __str__(self) -> str:
        if self.pet_service:
            service_name = self.pet_service.name
        elif self.vet_doctor:
            service_name = f"Dr. {self.vet_doctor.name}"
        else:
            service_name = "removed service"
        user_label = self.user.email or self.user.get_full_name() or str(self.user.pk)
        return f"Booking by {user_label} for {service_name} on {self.booking_date}"
