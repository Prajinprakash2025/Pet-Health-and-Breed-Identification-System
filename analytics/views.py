from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from collections import Counter
from datetime import date

def staff_required(view_func):
    return user_passes_test(
        lambda u: u.is_active and u.is_staff,
        login_url="/accounts/login/"
    )(view_func)
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.conf import settings
from pathlib import Path
import zipfile
import shutil
import json

from pets.models import Pet, BreedPrediction, HealthAssessment
from records.models import VaccinationRecord, MedicalRecord, Reminder
from advisory.models import (
    CareAdvisory,
    DiseaseInfo,
    MedicineRecommendation,
    PetService,
    ServiceBooking,
    VaccinationScheduleTemplate,
    VetDoctor,
    ContactMessage,
)


def _condition_from_assessment_notes(notes):
    if not notes:
        return "Unspecified"
    text = notes
    marker = "AI Health Detection:"
    if marker in text:
        text = text.split(marker, 1)[1]
    text = text.split("(", 1)[0].strip(" .:-")
    return text or "Unspecified"


def _pet_age_group(pet, today=None):
    if not pet.date_of_birth:
        return "Unknown age"
    today = today or date.today()
    years = today.year - pet.date_of_birth.year
    if (today.month, today.day) < (pet.date_of_birth.month, pet.date_of_birth.day):
        years -= 1
    if years < 1:
        return "0-1 year"
    if years < 3:
        return "1-3 years"
    if years < 7:
        return "3-7 years"
    return "7+ years"


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
    total_reminders = Reminder.objects.filter(pet__in=pet_ids).count()
    open_reminders = Reminder.objects.filter(pet__in=pet_ids, is_completed=False).count()

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

    upcoming_reminders = (
        Reminder.objects.filter(pet__in=pet_ids, is_completed=False)
        .select_related("pet")
        .order_by("due_date")[:5]
    )

    recent_bookings = (
        ServiceBooking.objects.filter(user=user)
        .select_related("pet_service", "vet_doctor")
        .order_by("-created_at")[:5]
    )

    context = {
        "active_section": "overview",
        "total_pets": total_pets,
        "total_dogs": total_dogs,
        "total_cats": total_cats,
        "total_predictions": total_predictions,
        "total_assessments": total_assessments,
        "total_vaccinations": total_vaccinations,
        "total_medical": total_medical,
        "total_reminders": total_reminders,
        "open_reminders": open_reminders,
        "breed_labels": json.dumps(breed_labels),
        "breed_counts": json.dumps(breed_counts),
        "species_labels": json.dumps(species_labels),
        "species_counts": json.dumps(species_counts),
        "health_labels": json.dumps(health_labels),
        "health_counts": json.dumps(health_counts),
        "vax_labels": json.dumps(vax_labels),
        "vax_counts": json.dumps(vax_counts),
        "recent_predictions": recent_predictions,
        "recent_assessments": recent_assessments,
        "upcoming_reminders": upcoming_reminders,
        "recent_bookings": recent_bookings,
        "pets": pets,
    }
    return render(request, "analytics/dashboard.html", context)


@login_required
def analytics_section_view(request):
    """Dedicated analytics page with all charts."""
    user = request.user
    pets = Pet.objects.filter(owner=user)
    pet_ids = pets.values_list("id", flat=True)

    breed_data = (
        BreedPrediction.objects.filter(pet__in=pet_ids)
        .values("predicted_breed")
        .annotate(count=Count("id"))
        .order_by("-count")[:10]
    )
    breed_labels = [b["predicted_breed"] for b in breed_data]
    breed_counts = [b["count"] for b in breed_data]

    species_data = pets.values("species").annotate(count=Count("id"))
    species_labels = [s["species"].title() for s in species_data]
    species_counts = [s["count"] for s in species_data]

    health_data = (
        HealthAssessment.objects.filter(pet__in=pet_ids)
        .values("overall_risk_level")
        .annotate(count=Count("id"))
    )
    health_labels = [h["overall_risk_level"].title() for h in health_data]
    health_counts = [h["count"] for h in health_data]

    vax_data = (
        VaccinationRecord.objects.filter(pet__in=pet_ids)
        .values("status")
        .annotate(count=Count("id"))
    )
    vax_labels = [v["status"].title() for v in vax_data]
    vax_counts = [v["count"] for v in vax_data]

    assessments = (
        HealthAssessment.objects.filter(pet__in=pet_ids)
        .select_related("pet")
    )
    disease_counter = Counter(_condition_from_assessment_notes(a.notes) for a in assessments)
    disease_labels = list(disease_counter.keys())
    disease_counts = list(disease_counter.values())

    today = date.today()
    age_counter = Counter(_pet_age_group(a.pet, today) for a in assessments)
    age_labels = ["0-1 year", "1-3 years", "3-7 years", "7+ years", "Unknown age"]
    age_counts = [age_counter.get(label, 0) for label in age_labels]

    clinic_data = (
        MedicalRecord.objects.filter(pet__in=pet_ids)
        .exclude(clinic_name="")
        .values("clinic_name")
        .annotate(count=Count("id"))
        .order_by("-count")[:10]
    )
    clinic_labels = [c["clinic_name"] for c in clinic_data]
    clinic_counts = [c["count"] for c in clinic_data]

    context = {
        "active_section": "analytics",
        "breed_labels": json.dumps(breed_labels),
        "breed_counts": json.dumps(breed_counts),
        "species_labels": json.dumps(species_labels),
        "species_counts": json.dumps(species_counts),
        "health_labels": json.dumps(health_labels),
        "health_counts": json.dumps(health_counts),
        "vax_labels": json.dumps(vax_labels),
        "vax_counts": json.dumps(vax_counts),
        "disease_labels": json.dumps(disease_labels),
        "disease_counts": json.dumps(disease_counts),
        "age_labels": json.dumps(age_labels),
        "age_counts": json.dumps(age_counts),
        "clinic_labels": json.dumps(clinic_labels),
        "clinic_counts": json.dumps(clinic_counts),
        "has_disease_data": bool(disease_counts),
        "has_age_data": any(age_counts),
        "has_clinic_data": bool(clinic_counts),
        "has_vax_data": bool(vax_counts),
        "has_species_data": bool(species_counts),
        "has_breed_data": bool(breed_counts),
        "has_health_data": bool(health_counts),
    }
    return render(request, "analytics/analytics.html", context)


@login_required
def health_section_view(request):
    """Dedicated health assessments page."""
    user = request.user
    pets = Pet.objects.filter(owner=user)
    pet_ids = pets.values_list("id", flat=True)

    assessments = (
        HealthAssessment.objects.filter(pet__in=pet_ids)
        .select_related("pet")
        .order_by("-assessment_date")
    )
    total_assessments = assessments.count()

    health_data = (
        HealthAssessment.objects.filter(pet__in=pet_ids)
        .values("overall_risk_level")
        .annotate(count=Count("id"))
    )
    health_labels = [h["overall_risk_level"].title() for h in health_data]
    health_counts = [h["count"] for h in health_data]

    low_risk_count = assessments.filter(overall_risk_level="low").count()
    medium_risk_count = assessments.filter(overall_risk_level="medium").count()
    high_risk_count = assessments.filter(overall_risk_level="high").count()

    context = {
        "active_section": "health",
        "assessments": assessments,
        "total_assessments": total_assessments,
        "health_labels": json.dumps(health_labels),
        "health_counts": json.dumps(health_counts),
        "low_risk_count": low_risk_count,
        "medium_risk_count": medium_risk_count,
        "high_risk_count": high_risk_count,
    }
    return render(request, "analytics/health.html", context)


@login_required
def records_section_view(request):
    """Dedicated medical records page."""
    user = request.user
    pets = Pet.objects.filter(owner=user)
    pet_ids = pets.values_list("id", flat=True)

    vaccinations = (
        VaccinationRecord.objects.filter(pet__in=pet_ids)
        .select_related("pet")
        .order_by("-scheduled_date")
    )
    medical_records = (
        MedicalRecord.objects.filter(pet__in=pet_ids)
        .select_related("pet")
        .order_by("-visit_date")
    )

    total_vaccinations = vaccinations.count()
    total_medical = medical_records.count()
    completed_vax = vaccinations.filter(status="completed").count()
    scheduled_vax = vaccinations.filter(status="scheduled").count()

    vax_data = (
        VaccinationRecord.objects.filter(pet__in=pet_ids)
        .values("status")
        .annotate(count=Count("id"))
    )
    vax_labels = [v["status"].title() for v in vax_data]
    vax_counts = [v["count"] for v in vax_data]

    context = {
        "active_section": "records",
        "vaccinations": vaccinations,
        "medical_records": medical_records,
        "total_vaccinations": total_vaccinations,
        "total_medical": total_medical,
        "completed_vax": completed_vax,
        "scheduled_vax": scheduled_vax,
        "vax_labels": json.dumps(vax_labels),
        "vax_counts": json.dumps(vax_counts),
    }
    return render(request, "analytics/records.html", context)


@login_required
def my_pets_section_view(request):
    """Dedicated My Pets page with larger cards."""
    user = request.user
    pets = Pet.objects.filter(owner=user)
    context = {
        "active_section": "my_pets",
        "pets": pets,
    }
    return render(request, "analytics/my_pets.html", context)


@login_required
def advisory_section_view(request):
    """Dashboard-shell veterinary advisory page."""
    species = request.GET.get("species", "").strip()
    category = request.GET.get("category", "").strip()

    advisories = CareAdvisory.objects.filter(is_active=True)
    vaccines = VaccinationScheduleTemplate.objects.all()

    if species in {"dog", "cat"}:
        advisories = advisories.filter(Q(species=species) | Q(species="both"))
        vaccines = vaccines.filter(species=species)
    if category:
        advisories = advisories.filter(category=category)

    context = {
        "advisories": advisories,
        "vaccines": vaccines.order_by("species", "recommended_age_weeks", "vaccine_name"),
        "species": species,
        "category": category,
        "species_choices": [("dog", "Dog"), ("cat", "Cat")],
        "category_choices": CareAdvisory.CATEGORY_CHOICES,
        "active_section": "advisory",
        "dashboard_mode": True,
    }
    return render(request, "advisory/advisory_home_dashboard.html", context)


@login_required
def medicine_section_view(request):
    """Dashboard-shell medicine recommendations page."""
    species = request.GET.get("species", "").strip()
    condition = request.GET.get("condition", "").strip()

    medicines = MedicineRecommendation.objects.filter(is_active=True)
    if species in {"dog", "cat"}:
        medicines = medicines.filter(Q(species=species) | Q(species="both"))
    if condition:
        medicines = medicines.filter(
            Q(condition_name__icontains=condition)
            | Q(medicine_name__icontains=condition)
            | Q(dosage_guidance__icontains=condition)
        )

    context = {
        "medicines": medicines,
        "species": species,
        "condition": condition,
        "species_choices": [("dog", "Dog"), ("cat", "Cat")],
        "active_section": "advisory",
        "dashboard_mode": True,
    }
    return render(request, "advisory/medicine_recommendations_dashboard.html", context)


@login_required
def services_section_view(request):
    """Dashboard-shell service finder page."""
    query = request.GET.get("q", "").strip()
    service_type = request.GET.get("type", "").strip()

    services = PetService.objects.filter(is_active=True)
    if service_type:
        services = services.filter(service_type=service_type)
    if query:
        services = services.filter(
            Q(name__icontains=query)
            | Q(city__icontains=query)
            | Q(address__icontains=query)
            | Q(notes__icontains=query)
        )

    doctors = VetDoctor.objects.filter(is_available=True)
    if query:
        doctors = doctors.filter(
            Q(name__icontains=query)
            | Q(clinic_name__icontains=query)
            | Q(address__icontains=query)
            | Q(specialization__icontains=query)
        )

    user_pets = Pet.objects.filter(owner=request.user)

    context = {
        "services": services,
        "doctors": doctors,
        "query": query,
        "service_type": service_type,
        "service_type_choices": PetService.SERVICE_TYPE_CHOICES,
        "active_section": "services",
        "dashboard_mode": True,
        "user_pets": user_pets,
    }
    return render(request, "advisory/service_finder_dashboard.html", context)


@login_required
def bookings_section_view(request):
    """Dedicated user booking history page."""
    bookings = (
        ServiceBooking.objects.filter(user=request.user)
        .select_related("pet_service", "vet_doctor")
        .order_by("-booking_date", "-booking_time", "-created_at")
    )

    context = {
        "active_section": "bookings",
        "bookings": bookings,
        "total_bookings": bookings.count(),
        "pending_bookings": bookings.filter(status="pending").count(),
        "confirmed_bookings": bookings.filter(status="confirmed").count(),
        "completed_bookings": bookings.filter(status="completed").count(),
    }
    return render(request, "analytics/bookings.html", context)


@staff_required
def ml_admin_dashboard(request):
    base_dir = Path(settings.BASE_DIR)
    User = get_user_model()
    datasets_root = base_dir / "ml_datasets"
    models_root = base_dir / "ml"
    datasets_root.mkdir(exist_ok=True, parents=True)
    models_root.mkdir(exist_ok=True, parents=True)

    dataset_dirs = [p for p in datasets_root.iterdir() if p.is_dir()]
    latest_dataset = max(dataset_dirs, key=lambda p: p.stat().st_mtime) if dataset_dirs else None

    users = User.objects.all().order_by("-is_superuser", "-is_staff", "username")
    doctors = VetDoctor.objects.all()

    if request.method == "POST":
        # ── User: Block ────────────────────────────────────────────────────
        if "block_user_id" in request.POST:
            user_id = request.POST.get("block_user_id")
            try:
                target = User.objects.get(pk=user_id)
                if target == request.user:
                    messages.warning(request, "You cannot block your own account.")
                else:
                    target.is_active = False
                    target.save()
                    messages.success(request, f"User '{target.username}' has been blocked.")
            except User.DoesNotExist:
                messages.error(request, "Selected user no longer exists.")
            return redirect("analytics:ml_admin_dashboard")

        # ── User: Unblock ──────────────────────────────────────────────────
        if "unblock_user_id" in request.POST:
            user_id = request.POST.get("unblock_user_id")
            try:
                target = User.objects.get(pk=user_id)
                target.is_active = True
                target.save()
                messages.success(request, f"User '{target.username}' has been unblocked.")
            except User.DoesNotExist:
                messages.error(request, "Selected user no longer exists.")
            return redirect("analytics:ml_admin_dashboard")

        # ── User: Promote to staff ─────────────────────────────────────────
        if "promote_user_id" in request.POST:
            user_id = request.POST.get("promote_user_id")
            try:
                target = User.objects.get(pk=user_id)
                target.is_staff = True
                target.save()
                messages.success(request, f"User '{target.username}' promoted to staff.")
            except User.DoesNotExist:
                messages.error(request, "Selected user no longer exists.")
            return redirect("analytics:ml_admin_dashboard")

        # ── User: Demote from staff ────────────────────────────────────────
        if "demote_user_id" in request.POST:
            user_id = request.POST.get("demote_user_id")
            try:
                target = User.objects.get(pk=user_id)
                if target == request.user:
                    messages.warning(request, "You cannot demote yourself.")
                else:
                    target.is_staff = False
                    target.save()
                    messages.success(request, f"User '{target.username}' demoted from staff.")
            except User.DoesNotExist:
                messages.error(request, "Selected user no longer exists.")
            return redirect("analytics:ml_admin_dashboard")

        # ── User: Delete ───────────────────────────────────────────────────
        if "delete_user_id" in request.POST:
            user_id = request.POST.get("delete_user_id")
            try:
                target = User.objects.get(pk=user_id)
                if target == request.user:
                    messages.warning(request, "You cannot delete your own account.")
                elif target.is_superuser:
                    messages.warning(request, "Cannot delete a superuser account.")
                else:
                    username = target.username
                    target.delete()
                    messages.success(request, f"User '{username}' has been deleted.")
            except User.DoesNotExist:
                messages.error(request, "Selected user no longer exists.")
            return redirect("analytics:ml_admin_dashboard")

        # ── Doctor: Add ────────────────────────────────────────────────────
        if "add_doctor" in request.POST:
            VetDoctor.objects.create(
                name=request.POST.get("doctor_name", "").strip(),
                specialization=request.POST.get("doctor_specialization", "general"),
                phone=request.POST.get("doctor_phone", "").strip(),
                email=request.POST.get("doctor_email", "").strip(),
                clinic_name=request.POST.get("doctor_clinic", "").strip(),
                address=request.POST.get("doctor_address", "").strip(),
                experience_years=int(request.POST.get("doctor_experience", 0) or 0),
                is_available="doctor_available" in request.POST,
                photo=request.FILES.get("doctor_photo"),
            )
            messages.success(request, "Doctor added successfully.")
            return redirect(reverse("analytics:ml_admin_dashboard") + "?panel=doctors")

        # ── Doctor: Edit ───────────────────────────────────────────────────
        if "edit_doctor_id" in request.POST:
            doc_id = request.POST.get("edit_doctor_id")
            try:
                doc = VetDoctor.objects.get(pk=doc_id)
                doc.name = request.POST.get("doctor_name", "").strip()
                doc.specialization = request.POST.get("doctor_specialization", "general")
                doc.phone = request.POST.get("doctor_phone", "").strip()
                doc.email = request.POST.get("doctor_email", "").strip()
                doc.clinic_name = request.POST.get("doctor_clinic", "").strip()
                doc.address = request.POST.get("doctor_address", "").strip()
                doc.experience_years = int(request.POST.get("doctor_experience", 0) or 0)
                doc.is_available = "doctor_available" in request.POST
                if request.FILES.get("doctor_photo"):
                    doc.photo = request.FILES["doctor_photo"]
                doc.save()
                messages.success(request, f"Dr. {doc.name} updated successfully.")
            except VetDoctor.DoesNotExist:
                messages.error(request, "Doctor not found.")
            return redirect("analytics:ml_admin_dashboard")

        # ── Doctor: Delete ─────────────────────────────────────────────────
        if "delete_doctor_id" in request.POST:
            doc_id = request.POST.get("delete_doctor_id")
            try:
                doc = VetDoctor.objects.get(pk=doc_id)
                name = doc.name
                doc.delete()
                messages.success(request, f"Dr. {name} has been removed.")
            except VetDoctor.DoesNotExist:
                messages.error(request, "Doctor not found.")
            return redirect("analytics:ml_admin_dashboard")

        # ── Doctor: Toggle availability ────────────────────────────────────
        if "toggle_doctor_id" in request.POST:
            doc_id = request.POST.get("toggle_doctor_id")
            try:
                doc = VetDoctor.objects.get(pk=doc_id)
                doc.is_available = not doc.is_available
                doc.save()
                status = "available" if doc.is_available else "unavailable"
                messages.success(request, f"Dr. {doc.name} marked as {status}.")
            except VetDoctor.DoesNotExist:
                messages.error(request, "Doctor not found.")
            return redirect("analytics:ml_admin_dashboard")

        # ── Service: Add ───────────────────────────────────────────────────
        if "add_service" in request.POST:
            PetService.objects.create(
                name=request.POST.get("service_name", "").strip(),
                service_type=request.POST.get("service_type", "vet"),
                city=request.POST.get("service_city", "").strip(),
                phone=request.POST.get("service_phone", "").strip(),
                email=request.POST.get("service_email", "").strip(),
                address=request.POST.get("service_address", "").strip(),
                website=request.POST.get("service_website", "").strip(),
                opening_hours=request.POST.get("service_hours", "").strip(),
                notes=request.POST.get("service_notes", "").strip(),
                is_active="service_active" in request.POST,
            )
            messages.success(request, "Pet service added successfully.")
            return redirect(reverse("analytics:ml_admin_dashboard") + "?panel=services")

        # ── Service: Edit ──────────────────────────────────────────────────
        if "edit_service_id" in request.POST:
            srv_id = request.POST.get("edit_service_id")
            try:
                srv = PetService.objects.get(pk=srv_id)
                srv.name = request.POST.get("service_name", "").strip()
                srv.service_type = request.POST.get("service_type", "vet")
                srv.city = request.POST.get("service_city", "").strip()
                srv.phone = request.POST.get("service_phone", "").strip()
                srv.email = request.POST.get("service_email", "").strip()
                srv.address = request.POST.get("service_address", "").strip()
                srv.website = request.POST.get("service_website", "").strip()
                srv.opening_hours = request.POST.get("service_hours", "").strip()
                srv.notes = request.POST.get("service_notes", "").strip()
                srv.is_active = "service_active" in request.POST
                srv.save()
                messages.success(request, f"Service '{srv.name}' updated successfully.")
            except PetService.DoesNotExist:
                messages.error(request, "Service not found.")
            return redirect("analytics:ml_admin_dashboard")

        # ── Service: Delete ────────────────────────────────────────────────
        if "delete_service_id" in request.POST:
            srv_id = request.POST.get("delete_service_id")
            try:
                srv = PetService.objects.get(pk=srv_id)
                name = srv.name
                srv.delete()
                messages.success(request, f"Service '{name}' has been removed.")
            except PetService.DoesNotExist:
                messages.error(request, "Service not found.")
            return redirect("analytics:ml_admin_dashboard")

        # ── Service: Toggle active ─────────────────────────────────────────
        if "toggle_service_id" in request.POST:
            srv_id = request.POST.get("toggle_service_id")
            try:
                srv = PetService.objects.get(pk=srv_id)
                srv.is_active = not srv.is_active
                srv.save()
                status = "active" if srv.is_active else "inactive"
                messages.success(request, f"Service '{srv.name}' marked as {status}.")
            except PetService.DoesNotExist:
                messages.error(request, "Service not found.")
            return redirect("analytics:ml_admin_dashboard")

        # ── Dataset upload ─────────────────────────────────────────────────
        if "dataset_zip" in request.FILES:
            upload = request.FILES["dataset_zip"]
            zip_name = upload.name.rsplit(".", 1)[0]
            target_dir = datasets_root / zip_name
            target_dir.mkdir(exist_ok=True, parents=True)

            temp_zip_path = target_dir.with_suffix(".zip")
            with open(temp_zip_path, "wb") as f:
                for chunk in upload.chunks():
                    f.write(chunk)

            try:
                with zipfile.ZipFile(temp_zip_path, "r") as zf:
                    zf.extractall(target_dir)

                # Check for single top-level folder (e.g., typical Kaggle zip)
                extracted_items = list(target_dir.iterdir())
                if len(extracted_items) == 1 and extracted_items[0].is_dir():
                    single_folder = extracted_items[0]
                    # Move everything up one level
                    for item in single_folder.iterdir():
                        shutil.move(str(item), str(target_dir / item.name))
                    single_folder.rmdir()

                # Validate dataset structure and count images
                valid_dataset = False
                breed_stats = {}
                image_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

                for item in target_dir.iterdir():
                    if item.is_dir():
                        images = [f for f in item.iterdir() if f.is_file() and f.suffix.lower() in image_extensions]
                        if images:
                            valid_dataset = True
                            breed_stats[item.name] = len(images)
                        else:
                            # Clean up empty or non-image folders
                            shutil.rmtree(item)

                if not valid_dataset:
                    shutil.rmtree(target_dir)
                    messages.error(request, "Invalid dataset format. No valid image classes found.")
                else:
                    total_imgs = sum(breed_stats.values())
                    messages.success(
                        request,
                        f"Dataset extracted successfully: {len(breed_stats)} breeds, {total_imgs} images."
                    )

            except zipfile.BadZipFile:
                messages.error(request, "Uploaded file is not a valid ZIP archive.")
                shutil.rmtree(target_dir, ignore_errors=True)
            finally:
                if temp_zip_path.exists():
                    temp_zip_path.unlink()

            return redirect("analytics:ml_admin_dashboard")

        # ── Booking: Update Status ──────────────────────────────────────────
        if "update_booking_status" in request.POST:
            booking_id = request.POST.get("booking_id")
            new_status = request.POST.get("status")
            admin_notes = request.POST.get("admin_notes", "").strip()
            try:
                booking = ServiceBooking.objects.get(pk=booking_id)
                booking.status = new_status
                if admin_notes:
                    booking.admin_notes = admin_notes
                booking.save()
                user_label = booking.user.email or booking.user.get_full_name() or str(booking.user.pk)
                messages.success(request, f"Booking for {user_label} updated to {new_status}.")
            except ServiceBooking.DoesNotExist:
                messages.error(request, "Booking not found.")
            return redirect(reverse("analytics:ml_admin_dashboard") + "?panel=bookings")

        # ── Contact: Toggle Read Status ────────────────────────────────────
        if "toggle_message_read" in request.POST:
            msg_id = request.POST.get("message_id")
            try:
                msg = ContactMessage.objects.get(pk=msg_id)
                msg.is_read = not msg.is_read
                msg.save()
                status = "read" if msg.is_read else "unread"
                messages.success(request, f"Message from {msg.first_name} marked as {status}.")
            except ContactMessage.DoesNotExist:
                messages.error(request, "Message not found.")
            return redirect(reverse("analytics:ml_admin_dashboard") + "?panel=contacts")

        # ── Training trigger ───────────────────────────────────────────────
        if "train_model" in request.POST:
            if latest_dataset is None:
                messages.error(request, "No dataset found. Upload a dataset ZIP first.")
            else:
                try:
                    from ml.trainer import train_from_directory

                    stats = train_from_directory(latest_dataset)
                    messages.success(
                        request,
                        f"Training complete. Train acc: {stats['train_accuracy']:.2%}, "
                        f"Val acc: {stats['val_accuracy']:.2%} on {stats['num_classes']} classes.",
                    )
                except Exception as exc:
                    messages.error(request, f"Training failed: {exc}")

            return redirect("analytics:ml_admin_dashboard")

    model_path = models_root / "pet_breed_model.keras"
    model_exists = model_path.exists()

    dataset_stats = {}
    total_images = 0
    if latest_dataset and latest_dataset.exists():
        image_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
        for item in latest_dataset.iterdir():
            if item.is_dir():
                num_images = sum(1 for f in item.iterdir() if f.is_file() and f.suffix.lower() in image_extensions)
                if num_images > 0:
                    dataset_stats[item.name] = num_images
        total_images = sum(dataset_stats.values())

    # ── Site-wide stats for overview ───────────────────────────────────────
    total_users      = users.count()
    active_users     = users.filter(is_active=True).count()
    blocked_users    = users.filter(is_active=False).count()
    staff_users      = users.filter(is_staff=True).count()
    total_pets       = Pet.objects.count()
    total_dogs       = Pet.objects.filter(species="dog").count()
    total_cats       = Pet.objects.filter(species="cat").count()
    total_predictions  = BreedPrediction.objects.count()
    total_assessments  = HealthAssessment.objects.count()
    total_vaccinations = VaccinationRecord.objects.count()
    total_medical      = MedicalRecord.objects.count()
    high_risk_count    = HealthAssessment.objects.filter(overall_risk_level="high").count()
    total_doctors      = doctors.count()
    available_doctors  = doctors.filter(is_available=True).count()

    # ── Species distribution for chart ─────────────────────────────────────
    species_data = Pet.objects.values("species").annotate(count=Count("id"))
    species_labels = [s["species"].title() for s in species_data]
    species_counts = [s["count"] for s in species_data]

    # ── Health risk distribution for chart ─────────────────────────────────
    health_data = (
        HealthAssessment.objects.values("overall_risk_level")
        .annotate(count=Count("id"))
    )
    health_labels = [h["overall_risk_level"].title() for h in health_data]
    health_counts = [h["count"] for h in health_data]

    # ── Per-user stats for reports ─────────────────────────────────────────
    user_stats = (
        User.objects.annotate(
            pet_count=Count("pets", distinct=True),
        )
        .order_by("-date_joined")
    )

    # ── High/medium risk assessments for reports ───────────────────────────
    risk_assessments = (
        HealthAssessment.objects.filter(overall_risk_level__in=["high", "medium"])
        .select_related("pet", "pet__owner")
        .order_by("-assessment_date")[:20]
    )

    # ── Recent activity ────────────────────────────────────────────────────
    recent_users = users.order_by("-date_joined")[:8]
    recent_predictions_all = (
        BreedPrediction.objects.select_related("pet", "pet__owner")
        .order_by("-created_at")[:8]
    )

    # ── Specialization choices for doctor form ─────────────────────────────
    specialization_choices = VetDoctor.SPECIALIZATION_CHOICES
    
    # ── Services and Service type choices for service form ─────────────────
    services = PetService.objects.all()
    service_type_choices = PetService.SERVICE_TYPE_CHOICES

    # ── Bookings for management ────────────────────────────────────────────
    all_bookings = ServiceBooking.objects.all().select_related("user", "pet_service", "vet_doctor").order_by("-created_at")
    booking_status_choices = ServiceBooking.STATUS_CHOICES

    context = {
        "model_exists": model_exists,
        "latest_dataset": latest_dataset.name if latest_dataset else None,
        "dataset_stats_display": dataset_stats,
        "total_images": total_images,
        "datasets": [p.name for p in dataset_dirs],
        "users": users,
        "doctors": doctors,
        "services": services,
        "all_bookings": all_bookings,
        "contact_messages": ContactMessage.objects.all(),
        "booking_status_choices": booking_status_choices,
        "specialization_choices": specialization_choices,
        "service_type_choices": service_type_choices,
        # overview stats
        "total_users": total_users,
        "active_users": active_users,
        "blocked_users": blocked_users,
        "staff_users": staff_users,
        "total_pets": total_pets,
        "total_dogs": total_dogs,
        "total_cats": total_cats,
        "total_predictions": total_predictions,
        "total_assessments": total_assessments,
        "total_vaccinations": total_vaccinations,
        "total_medical": total_medical,
        "high_risk_count": high_risk_count,
        "total_doctors": total_doctors,
        "available_doctors": available_doctors,
        # charts
        "species_labels": json.dumps(species_labels),
        "species_counts": json.dumps(species_counts),
        "health_labels": json.dumps(health_labels),
        "health_counts": json.dumps(health_counts),
        # recent activity
        "recent_users": recent_users,
        "recent_predictions_all": recent_predictions_all,
        # reports
        "user_stats": user_stats,
        "risk_assessments": risk_assessments,
    }

    return render(request, "admin/ml_dashboard.html", context)
