import random
import time
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import PetForm, MissingPetForm, PetSightingForm
from .models import BreedPrediction, HealthAssessment, Pet, MissingPet, PetSighting


# ── Breed-specific health risk data (demo) ─────────────────────────────────
# Maps breed names to typical health risks. Unknown breeds get a default.
BREED_HEALTH_RISKS = {
    "Golden Retriever": {"skin_infection_risk": "medium", "fur_loss_risk": "medium", "obesity_risk": "high"},
    "German Shepherd": {"skin_infection_risk": "medium", "parasite_risk": "medium"},
    "Labrador Retriever": {"obesity_risk": "high", "eye_issue_risk": "low"},
    "Poodle": {"eye_issue_risk": "medium", "fur_loss_risk": "low"},
    "Bulldog": {"skin_infection_risk": "high", "wound_risk": "medium", "obesity_risk": "high"},
    "Beagle": {"obesity_risk": "medium", "parasite_risk": "medium"},
    "Rottweiler": {"obesity_risk": "medium", "wound_risk": "medium"},
    "Yorkshire Terrier": {"fur_loss_risk": "medium", "eye_issue_risk": "medium"},
    "Boxer": {"skin_infection_risk": "medium", "wound_risk": "medium"},
    "Persian": {"eye_issue_risk": "high", "fur_loss_risk": "medium"},
    "Siamese": {"eye_issue_risk": "medium", "skin_infection_risk": "low"},
    "Maine Coon": {"obesity_risk": "medium", "fur_loss_risk": "low"},
    "Bengal": {"skin_infection_risk": "low", "parasite_risk": "medium"},
    "Sphynx": {"skin_infection_risk": "high", "eye_issue_risk": "medium"},
    "British Shorthair": {"obesity_risk": "high"},
    "Ragdoll": {"fur_loss_risk": "medium"},
    "Russian Blue": {"obesity_risk": "medium"},
    "Abyssinian": {"parasite_risk": "medium"},
}


def _calculate_overall_risk(assessment: HealthAssessment) -> str:
    """Derive overall risk from individual risk fields."""
    risk_values = {
        "low": 1,
        "medium": 2,
        "high": 3,
    }
    fields = [
        assessment.skin_infection_risk,
        assessment.fur_loss_risk,
        assessment.eye_issue_risk,
        assessment.wound_risk,
        assessment.parasite_risk,
        assessment.obesity_risk,
    ]
    avg = sum(risk_values.get(f, 1) for f in fields) / len(fields)
    if avg >= 2.5:
        return "high"
    elif avg >= 1.5:
        return "medium"
    return "low"


# ── Views ──────────────────────────────────────────────────────────────────
@login_required
def pet_list_view(request):
    pets = Pet.objects.filter(owner=request.user)
    return render(request, "pets/pet_list.html", {"pets": pets, "active_section": "my_pets"})


@login_required
def pet_detail_view(request, pet_id):
    pet = get_object_or_404(Pet, id=pet_id, owner=request.user)
    breed_prediction = pet.breed_predictions.first()
    health_assessment = pet.health_assessments.first()
    context = {
        "pet": pet,
        "breed_prediction": breed_prediction,
        "health_assessment": health_assessment,
        "active_section": "my_pets",
    }
    return render(request, "pets/pet_detail.html", context)


@login_required
def pet_add_view(request):
    dashboard_mode = request.path.startswith("/dashboard/")
    if request.method == "POST":
        form = PetForm(request.POST, request.FILES)
        if form.is_valid():
            pet = form.save(commit=False)
            pet.owner = request.user
            pet.save()
            messages.success(request, f"{pet.name} has been added to your pets.")
            if dashboard_mode:
                return redirect("analytics:my_pets_section")
            return redirect("pets:pet_detail", pet_id=pet.id)
    else:
        form = PetForm()
    template_name = "pets/pet_form_dashboard.html" if dashboard_mode else "pets/pet_form.html"
    return render(
        request,
        template_name,
        {"form": form, "active_section": "add_pet", "dashboard_mode": dashboard_mode},
    )


@login_required
def pet_edit_view(request, pet_id):
    dashboard_mode = request.path.startswith("/dashboard/")
    pet = get_object_or_404(Pet, id=pet_id, owner=request.user)
    if request.method == "POST":
        form = PetForm(request.POST, request.FILES, instance=pet)
        if form.is_valid():
            form.save()
            messages.success(request, f"{pet.name}'s profile has been updated.")
            return redirect("pets:pet_detail", pet_id=pet.id)
    else:
        form = PetForm(instance=pet)
    template_name = "pets/pet_form_dashboard.html" if dashboard_mode else "pets/pet_form.html"
    return render(
        request,
        template_name,
        {"form": form, "pet": pet, "active_section": "my_pets", "dashboard_mode": dashboard_mode},
    )


@require_POST
@login_required
def run_breed_prediction_view(request, pet_id):
    pet = get_object_or_404(Pet, id=pet_id, owner=request.user)

    if not pet.image:
        messages.error(request, "Cannot run prediction without a pet image.")
        return redirect("pets:pet_detail", pet_id=pet.id)

    # ── Real ML Model Inference ────────────────────────────────────────────
    started_at = time.perf_counter()
    try:
        from .ml_predictor import predict_breed
        breed_result = predict_breed(pet.image.path)
        predicted_breed = breed_result["breed"]
        species = breed_result["species"]
        confidence = breed_result["confidence"]
        low_confidence = breed_result.get("low_confidence", confidence < 80)
        top_predictions = breed_result.get("top_predictions", [])
        model_version = "1.0.0-efficientnetb0"
    except Exception as e:
        messages.warning(request, f"AI model error ({e}).")
        predicted_breed = "Unknown"
        species = pet.species
        confidence = 0.0
        low_confidence = True
        top_predictions = []
        model_version = "0.1.0-fallback"

    elapsed = time.perf_counter() - started_at
    print(
        "[breed-predict] "
        f"pet_id={pet.id} result={predicted_breed} "
        f"confidence={confidence:.1f}% elapsed={elapsed:.2f}s"
    )

    BreedPrediction.objects.create(
        pet=pet,
        predicted_breed=(
            f"Uncertain ({predicted_breed})"
            if low_confidence and predicted_breed != "Unknown"
            else predicted_breed
        ),
        species=species,
        confidence=confidence,
        model_version=model_version,
    )

    if predicted_breed == "Unknown":
        messages.warning(request, f"AI could not identify {pet.name}'s breed from this image.")
    elif low_confidence:
        alternatives = ", ".join(
            f"{item['breed']} {item['confidence']:.1f}%"
            for item in top_predictions[:3]
        )
        messages.warning(
            request,
            (
                f"AI is not confident for {pet.name}. Closest trained match: "
                f"{predicted_breed} ({confidence:.1f}%)."
                + (f" Top options: {alternatives}." if alternatives else "")
            ),
        )
    else:
        if not pet.breed:
            pet.breed = predicted_breed
            pet.save(update_fields=["breed"])
        messages.success(request, f"AI identified {pet.name} as a {predicted_breed} ({confidence:.1f}% confidence).")
    return redirect("pets:pet_detail", pet_id=pet.id)


@login_required
def breed_identify_view(request, pet_id):
    pet = get_object_or_404(Pet, id=pet_id, owner=request.user)
    breed_prediction = pet.breed_predictions.first()
    return render(
        request,
        "pets/breed_identify.html",
        {"pet": pet, "breed_prediction": breed_prediction, "active_section": "my_pets"},
    )


@login_required
def health_scan_view(request, pet_id):
    pet = get_object_or_404(Pet, id=pet_id, owner=request.user)
    assessment = pet.health_assessments.first()
    return render(
        request,
        "pets/health_scan.html",
        {"pet": pet, "health_assessment": assessment, "active_section": "my_pets"},
    )


@require_POST
@login_required
def run_health_prediction_view(request, pet_id):
    pet = get_object_or_404(Pet, id=pet_id, owner=request.user)

    uploaded_image = request.FILES.get("scan_image")
    symptom_details = request.POST.get("symptom_details", "").strip()
    
    # We need an image to scan: either the newly uploaded one, or the pet's default profile picture
    if not uploaded_image and not pet.image:
        messages.error(request, "Cannot run prediction without a pet image.")
        return redirect("pets:health_scan", pet_id=pet.id)

    # Resolve target image path
    if uploaded_image:
        assessment = HealthAssessment(pet=pet)
        assessment.scan_image = uploaded_image
        assessment.symptom_details = symptom_details
        assessment.save()
        target_path = assessment.scan_image.path
    else:
        assessment = HealthAssessment(pet=pet, symptom_details=symptom_details)
        target_path = pet.image.path

    try:
        from .ml_predictor import predict_health
        health_result = predict_health(target_path)
        predicted_disease = health_result["disease"]
        disease_desc = health_result["description"]
        health_conf = health_result["confidence"]
    except Exception as e:
        messages.warning(request, f"AI model error ({e}).")
        predicted_disease = "Healthy"
        disease_desc = "Healthy"
        health_conf = 0.0

    skin_risk = "low"
    fur_risk = "low"
    parasite_risk = "low"
    notes = f"AI Health Detection: {disease_desc} ({health_conf}% confidence)."
    care = ""

    if predicted_disease == "Scabies_Mange":
        skin_risk = "high"
        parasite_risk = "high"
        fur_risk = "high"
        care = "• Isolate your pet to prevent spreading mites to other animals or humans.\n• Avoid direct contact without gloves.\n• Consult a vet immediately for anti-parasitic dips, oral medications, or topical treatments.\n• Thoroughly clean its bedding, collars, and your home."
    elif predicted_disease == "Fungal_Infections":
        skin_risk = "high"
        fur_risk = "medium"
        care = "• Fungal infections (like Ringworm) are highly contagious. Isolate the pet.\n• Wash your hands thoroughly after handling.\n• Keep the affected area clean and dry.\n• Schedule a vet visit for prescriptive anti-fungal shampoos or medication."
    elif predicted_disease == "Bacterial_Dermatosis":
        skin_risk = "high"
        fur_risk = "medium"
        care = "• Keep the affected skin clean and dry. Do not let the pet lick or scratch the area (use an E-collar if necessary).\n• Bacterial infections often require antibiotics; seek veterinary care for proper diagnosis.\n• Avoid using human creams or ointments without vet approval."
    elif predicted_disease == "Allergic_Dermatitis":
        skin_risk = "medium"
        fur_risk = "medium"
        care = "• Check for fleas, as flea allergy is a common cause. Ensure flea preventatives are up to date.\n• Review recent changes in diet or environment (new shampoos, pollen, food).\n• A vet can provide antihistamines or corticosteroids to instantly relieve the itching."
    else:
        care = "• Maintain regular grooming and bathing.\n• Keep up with routine vaccinations and flea/tick preventatives.\n• Ensure a balanced diet and regular exercise.\n• Schedule an annual wellness checkup with your veterinarian."

    assessment.skin_infection_risk = skin_risk
    assessment.fur_loss_risk = fur_risk
    assessment.eye_issue_risk = "low"
    assessment.wound_risk = "low"
    assessment.parasite_risk = parasite_risk
    assessment.obesity_risk = "low"
    assessment.notes = notes
    assessment.care_recommendations = care
    assessment.overall_risk_level = _calculate_overall_risk(assessment)
    assessment.save()

    messages.success(request, f"AI Health Scan complete for {pet.name}.")
    return redirect("pets:health_scan", pet_id=pet.id)


def missing_pets_list_view(request):
    """Public list of missing pets with search functionality."""
    query = request.GET.get("q", "")
    species = request.GET.get("species", "")
    
    reports = MissingPet.objects.filter(is_found=False)
    
    if query:
        reports = reports.filter(
            Q(last_seen_location__icontains=query) | 
            Q(pet_name__icontains=query) | 
            Q(breed__icontains=query)
        )
    
    if species:
        reports = reports.filter(species=species)
        
    import json
    from django.urls import reverse
    map_markers = []
    for report in reports:
        if report.last_seen_lat and report.last_seen_lng:
            map_markers.append({
                "id": report.id,
                "lat": report.last_seen_lat,
                "lng": report.last_seen_lng,
                "name": report.pet_name,
                "species": report.get_species_display(),
                "location": report.last_seen_location,
                "photo_url": report.photo.url if report.photo else "",
                "detail_url": reverse('pets:missing_pet_detail', args=[report.id])
            })
            
    context = {
        "reports": reports,
        "query": query,
        "species_filter": species,
        "active_section": "missing_pets",
        "map_markers_data": map_markers
    }
    return render(request, "pets/missing_pets_list.html", context)


@login_required
def report_missing_view(request):
    """User view to report their pet as missing."""
    if request.method == "POST":
        form = MissingPetForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            report = form.save(commit=False)
            report.owner = request.user
            report.save()
            messages.success(request, f"Missing report for {report.pet_name} has been published.")
            return redirect("pets:missing_pets_list")
    else:
        # Pre-fill species if a pet is selected via GET param
        initial = {}
        pet_id = request.GET.get("pet_id")
        if pet_id:
            pet = get_object_or_404(Pet, id=pet_id, owner=request.user)
            initial = {"pet": pet, "pet_name": pet.name, "species": pet.species, "breed": pet.breed}
        
        form = MissingPetForm(user=request.user, initial=initial)
        
    import json
    user_pets = Pet.objects.filter(owner=request.user)
    pets_data = {
        pet.id: {
            "name": pet.name,
            "species": pet.species,
            "breed": pet.breed
        } for pet in user_pets
    }
    pets_json = json.dumps(pets_data)
        
    return render(request, "pets/report_missing.html", {
        "form": form, 
        "active_section": "missing_pets",
        "pets_json": pets_json
    })


def missing_pet_detail_view(request, report_id):
    """Detail view for a missing pet report with sighting form."""
    report = get_object_or_404(MissingPet, id=report_id)
    sightings = report.sightings.all()
    
    if request.method == "POST":
        sighting_form = PetSightingForm(request.POST, request.FILES)
        if sighting_form.is_valid():
            sighting = sighting_form.save(commit=False)
            sighting.missing_pet = report
            sighting.save()
            messages.success(request, "Thank you! Your sighting report has been submitted.")
            return redirect("pets:missing_pet_detail", report_id=report.id)
    else:
        sighting_form = PetSightingForm()
        
    context = {
        "report": report,
        "sightings": sightings,
        "sighting_form": sighting_form,
        "active_section": "missing_pets"
    }
    return render(request, "pets/missing_pet_detail.html", context)

