from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg
from django.shortcuts import render

from pets.models import Pet, BreedPrediction, HealthAssessment
from records.models import VaccinationRecord, MedicalRecord


@login_required
def dashboard_view(request):
    """Analytics dashboard with charts and statistics."""
    user = request.user
    pets = Pet.objects.filter(owner=user)
    pet_ids = pets.values_list("id", flat=True)

    # ── Summary stats ──────────────────────────────────────────────────────
    total_pets = pets.count()
    total_dogs = pets.filter(species="dog").count()
    total_cats = pets.filter(species="cat").count()
    total_predictions = BreedPrediction.objects.filter(pet__in=pet_ids).count()
    total_assessments = HealthAssessment.objects.filter(pet__in=pet_ids).count()
    total_vaccinations = VaccinationRecord.objects.filter(pet__in=pet_ids).count()
    total_medical = MedicalRecord.objects.filter(pet__in=pet_ids).count()

    # ── Breed distribution (for chart) ─────────────────────────────────────
    breed_data = (
        BreedPrediction.objects.filter(pet__in=pet_ids)
        .values("predicted_breed")
        .annotate(count=Count("id"))
        .order_by("-count")[:10]
    )
    breed_labels = [b["predicted_breed"] for b in breed_data]
    breed_counts = [b["count"] for b in breed_data]

    # ── Species distribution ───────────────────────────────────────────────
    species_data = pets.values("species").annotate(count=Count("id"))
    species_labels = [s["species"].title() for s in species_data]
    species_counts = [s["count"] for s in species_data]

    # ── Health risk distribution ───────────────────────────────────────────
    health_data = (
        HealthAssessment.objects.filter(pet__in=pet_ids)
        .values("overall_risk_level")
        .annotate(count=Count("id"))
    )
    health_labels = [h["overall_risk_level"].title() for h in health_data]
    health_counts = [h["count"] for h in health_data]

    # ── Vaccination compliance ─────────────────────────────────────────────
    vax_data = (
        VaccinationRecord.objects.filter(pet__in=pet_ids)
        .values("status")
        .annotate(count=Count("id"))
    )
    vax_labels = [v["status"].title() for v in vax_data]
    vax_counts = [v["count"] for v in vax_data]

    # ── Recent predictions ──────────────────────────────────────────────
    recent_predictions = (
        BreedPrediction.objects.filter(pet__in=pet_ids)
        .select_related("pet")
        .order_by("-created_at")[:5]
    )

    # ── Recent health assessments ──────────────────────────────────────
    recent_assessments = (
        HealthAssessment.objects.filter(pet__in=pet_ids)
        .select_related("pet")
        .order_by("-assessment_date")[:5]
    )

    context = {
        "total_pets": total_pets,
        "total_dogs": total_dogs,
        "total_cats": total_cats,
        "total_predictions": total_predictions,
        "total_assessments": total_assessments,
        "total_vaccinations": total_vaccinations,
        "total_medical": total_medical,
        "breed_labels": breed_labels,
        "breed_counts": breed_counts,
        "species_labels": species_labels,
        "species_counts": species_counts,
        "health_labels": health_labels,
        "health_counts": health_counts,
        "vax_labels": vax_labels,
        "vax_counts": vax_counts,
        "recent_predictions": recent_predictions,
        "recent_assessments": recent_assessments,
        "pets": pets,
    }
    return render(request, "analytics/dashboard.html", context)
