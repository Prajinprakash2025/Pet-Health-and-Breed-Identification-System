from django.contrib import admin

from .models import BreedPrediction, HealthAssessment, Pet, MissingPet, PetSighting


@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "species", "breed", "weight_kg", "created_at")
    list_filter = ("species", "created_at")
    search_fields = ("name", "breed", "owner__username", "owner__email")


@admin.register(BreedPrediction)
class BreedPredictionAdmin(admin.ModelAdmin):
    list_display = ("pet", "predicted_breed", "species", "confidence", "created_at")
    list_filter = ("species", "created_at")
    search_fields = ("pet__name", "predicted_breed", "model_version")


@admin.register(HealthAssessment)
class HealthAssessmentAdmin(admin.ModelAdmin):
    list_display = ("pet", "overall_risk_level", "assessment_date")
    list_filter = ("overall_risk_level", "assessment_date")
    search_fields = ("pet__name", "notes", "symptom_details", "care_recommendations")


@admin.register(MissingPet)
class MissingPetAdmin(admin.ModelAdmin):
    list_display = ("pet_name", "owner", "species", "last_seen_location", "is_found", "created_at")
    list_filter = ("species", "is_found", "created_at")
    search_fields = ("pet_name", "breed", "last_seen_location", "owner__username")
    list_editable = ("is_found",)


@admin.register(PetSighting)
class PetSightingAdmin(admin.ModelAdmin):
    list_display = ("missing_pet", "sighting_location", "sighting_date", "created_at")
    list_filter = ("sighting_date", "created_at")
    search_fields = ("missing_pet__pet_name", "sighting_location", "description")
