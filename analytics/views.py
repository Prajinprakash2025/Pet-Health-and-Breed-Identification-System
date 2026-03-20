from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import redirect, render
from django.conf import settings
from pathlib import Path
import zipfile
import shutil

from pets.models import Pet, BreedPrediction, HealthAssessment
from ml.trainer import DATASETS_DIR, train_from_directory
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
        "active_section": "overview",
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

    context = {
        "active_section": "analytics",
        "breed_labels": breed_labels,
        "breed_counts": breed_counts,
        "species_labels": species_labels,
        "species_counts": species_counts,
        "health_labels": health_labels,
        "health_counts": health_counts,
        "vax_labels": vax_labels,
        "vax_counts": vax_counts,
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
        "health_labels": health_labels,
        "health_counts": health_counts,
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
        "vax_labels": vax_labels,
        "vax_counts": vax_counts,
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


@staff_member_required
def ml_admin_dashboard(request):
    """
    Simple ML admin dashboard for uploading datasets and training the CNN model.
    """
    base_dir = Path(settings.BASE_DIR)
    User = get_user_model()
    datasets_root = DATASETS_DIR
    models_root = base_dir / "ml"
    datasets_root.mkdir(exist_ok=True, parents=True)
    models_root.mkdir(exist_ok=True, parents=True)

    # Determine latest dataset folder (if any)
    dataset_dirs = [p for p in datasets_root.iterdir() if p.is_dir()]
    latest_dataset = max(dataset_dirs, key=lambda p: p.stat().st_mtime) if dataset_dirs else None

    # All users for admin "Users" tab
    users = User.objects.all().order_by("-is_staff", "-is_superuser", "username")

    if request.method == "POST":
        # Handle user block / unblock
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

        # Handle dataset upload
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

        # Handle training trigger
        if "train_model" in request.POST:
            if latest_dataset is None:
                messages.error(request, "No dataset found. Upload a dataset ZIP first.")
            else:
                try:
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

    context = {
        "model_exists": model_exists,
        "model_path": model_path.name if model_exists else None,
        "latest_dataset": latest_dataset.name if latest_dataset else None,
        "dataset_stats": dataset_stats,
        "total_images": total_images,
        "datasets": [p.name for p in dataset_dirs],
        "users": users,
    }
    return render(request, "admin/ml_dashboard.html", context)
