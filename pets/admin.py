from django.contrib import admin

from .models import BreedPrediction, HealthAssessment, Pet


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
