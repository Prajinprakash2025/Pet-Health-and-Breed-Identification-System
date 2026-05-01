from django.contrib import admin

from .models import (
    BreedInfo,
    CareAdvisory,
    DiseaseInfo,
    MedicineRecommendation,
    PetService,
    VaccinationScheduleTemplate,
    VetDoctor,
)


@admin.register(BreedInfo)
class BreedInfoAdmin(admin.ModelAdmin):
    list_display = ("breed_name", "species", "temperament")
    list_filter = ("species",)
    search_fields = ("breed_name", "description", "temperament")


@admin.register(DiseaseInfo)
class DiseaseInfoAdmin(admin.ModelAdmin):
    list_display = ("name", "species")
    list_filter = ("species",)
    search_fields = ("name", "common_symptoms", "prevention", "treatment")


@admin.register(VaccinationScheduleTemplate)
class VaccinationScheduleTemplateAdmin(admin.ModelAdmin):
    list_display = ("vaccine_name", "species", "recommended_age_weeks", "repeat_interval_weeks")
    list_filter = ("species",)
    search_fields = ("vaccine_name", "notes")


@admin.register(CareAdvisory)
class CareAdvisoryAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "species", "is_active", "updated_at")
    list_filter = ("category", "species", "is_active")
    search_fields = ("title", "short_summary", "recommendation")


@admin.register(MedicineRecommendation)
class MedicineRecommendationAdmin(admin.ModelAdmin):
    list_display = ("medicine_name", "condition_name", "species", "is_active")
    list_filter = ("species", "is_active")
    search_fields = ("medicine_name", "condition_name", "dosage_guidance", "warnings")


@admin.register(PetService)
class PetServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "service_type", "city", "phone", "is_active")
    list_filter = ("service_type", "city", "is_active")
    search_fields = ("name", "city", "address", "phone", "email")


@admin.register(VetDoctor)
class VetDoctorAdmin(admin.ModelAdmin):
    list_display = ("name", "specialization", "clinic_name", "phone", "is_available")
    list_filter = ("specialization", "is_available")
    search_fields = ("name", "clinic_name", "email")
