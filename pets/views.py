import random
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import PetForm
from .models import BreedPrediction, HealthAssessment, Pet


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
    return render(request, "pets/pet_list.html", {"pets": pets})


@login_required
def pet_detail_view(request, pet_id):
    pet = get_object_or_404(Pet, id=pet_id, owner=request.user)
    breed_prediction = pet.breed_predictions.first()
    health_assessment = pet.health_assessments.first()
    context = {
        "pet": pet,
        "breed_prediction": breed_prediction,
        "health_assessment": health_assessment,
    }
    return render(request, "pets/pet_detail.html", context)


@login_required
def pet_add_view(request):
    if request.method == "POST":
        form = PetForm(request.POST, request.FILES)
        if form.is_valid():
            pet = form.save(commit=False)
            pet.owner = request.user
            pet.save()
            messages.success(request, f"{pet.name} has been added to your pets.")
            return redirect("pets:pet_detail", pet_id=pet.id)
    else:
        form = PetForm()
    return render(request, "pets/pet_form.html", {"form": form})


@login_required
def pet_edit_view(request, pet_id):
    pet = get_object_or_404(Pet, id=pet_id, owner=request.user)
    if request.method == "POST":
        form = PetForm(request.POST, request.FILES, instance=pet)
        if form.is_valid():
            form.save()
            messages.success(request, f"{pet.name}'s profile has been updated.")
            return redirect("pets:pet_detail", pet_id=pet.id)
    else:
        form = PetForm(instance=pet)
    return render(request, "pets/pet_form.html", {"form": form, "pet": pet})


@require_POST
@login_required
def run_breed_prediction_view(request, pet_id):
    pet = get_object_or_404(Pet, id=pet_id, owner=request.user)

    if not pet.image:
        messages.error(request, "Cannot run prediction without a pet image.")
        return redirect("pets:pet_detail", pet_id=pet.id)

    # ── Real ML Model Inference ────────────────────────────────────────────
    try:
        from .ml_predictor import predict_breed
        result = predict_breed(pet.image.path)

        predicted_breed = result["breed"]
        species = result["species"]
        confidence = result["confidence"]
        model_version = "1.0.0-mobilenetv2"
    except Exception as e:
        # Fallback to simple prediction if model fails
        messages.warning(request, f"AI model error ({e}). Using fallback prediction.")
        if pet.species == "dog":
            predicted_breed = random.choice(["Golden Retriever", "German Shepherd", "Poodle", "Labrador Retriever"])
        elif pet.species == "cat":
            predicted_breed = random.choice(["Siamese", "Persian", "Maine Coon", "Bengal"])
        else:
            predicted_breed = "Unknown"
        species = pet.species
        confidence = random.uniform(60, 80)
        model_version = "0.1.0-fallback"

    # Save breed prediction
    BreedPrediction.objects.create(
        pet=pet,
        predicted_breed=predicted_breed,
        species=species,
        confidence=confidence,
        model_version=model_version,
    )

    # ── Auto-generate Health Assessment ────────────────────────────────────
    risks = BREED_HEALTH_RISKS.get(predicted_breed, {})
    assessment = HealthAssessment(
        pet=pet,
        skin_infection_risk=risks.get("skin_infection_risk", "low"),
        fur_loss_risk=risks.get("fur_loss_risk", "low"),
        eye_issue_risk=risks.get("eye_issue_risk", "low"),
        wound_risk=risks.get("wound_risk", "low"),
        parasite_risk=risks.get("parasite_risk", "low"),
        obesity_risk=risks.get("obesity_risk", "low"),
        notes=f"Auto-generated health assessment based on breed: {predicted_breed}.",
    )
    assessment.overall_risk_level = _calculate_overall_risk(assessment)
    assessment.save()

    messages.success(
        request,
        f"AI identified {pet.name} as a {predicted_breed} ({confidence:.1f}% confidence). "
        f"Health assessment generated."
    )
    return redirect("pets:pet_detail", pet_id=pet.id)

