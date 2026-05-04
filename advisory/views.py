from django.contrib.auth.decorators import login_required
from django.db.models import Q
from pets.models import Pet

from .models import (
    CareAdvisory,
    MedicineRecommendation,
    PetService,
    VaccinationScheduleTemplate,
    VetDoctor,
    ServiceBooking,
)
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme


def _booking_redirect_url(request):
    next_url = request.POST.get("next", "")
    if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return next_url
    return "advisory:service_finder"


@login_required
def advisory_home(request):
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
    }
    return render(request, "advisory/advisory_home.html", context)


@login_required
def medicine_recommendations(request):
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
    }
    return render(request, "advisory/medicine_recommendations.html", context)


@login_required
def service_finder(request):
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
    if service_type and service_type != "vet":
        # If a specific non-vet service is selected, don't show doctors
        doctors = doctors.none()
    
    if query and doctors.exists():
        doctors = doctors.filter(
            Q(name__icontains=query)
            | Q(clinic_name__icontains=query)
            | Q(address__icontains=query)
            | Q(specialization__icontains=query)
        )

    user_pets = Pet.objects.filter(owner=request.user) if request.user.is_authenticated else Pet.objects.none()

    context = {
        "services": services,
        "doctors": doctors,
        "query": query,
        "service_type": service_type,
        "service_type_choices": PetService.SERVICE_TYPE_CHOICES,
        "active_section": "services",
        "user_pets": user_pets,
    }
    return render(request, "advisory/service_finder.html", context)


@login_required
def book_service(request):
    if request.method == "POST":
        service_id = request.POST.get("service_id")
        doctor_id = request.POST.get("doctor_id")
        pet_id = request.POST.get("pet_id")
        date = request.POST.get("date")
        time = request.POST.get("time")
        notes = request.POST.get("notes", "")

        if not date or not time:
            messages.error(request, "Please select both date and time for your booking.")
            return redirect(_booking_redirect_url(request))

        booking = ServiceBooking(
            user=request.user,
            booking_date=date,
            booking_time=time,
            notes=notes
        )
        if pet_id:
            booking.pet_id = pet_id
        if service_id:
            booking.pet_service_id = service_id
        if doctor_id:
            booking.vet_doctor_id = doctor_id
        
        booking.save()
        messages.success(request, "Your booking request has been submitted successfully! You can track its status in your dashboard.")
        return redirect(_booking_redirect_url(request))
    
    return redirect("advisory:service_finder")


def contact(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        subject = request.POST.get("subject")
        message = request.POST.get("message")

        if not all([first_name, last_name, email, subject, message]):
            messages.error(request, "Please fill in all fields.")
        else:
            ContactMessage.objects.create(
                first_name=first_name,
                last_name=last_name,
                email=email,
                subject=subject,
                message=message
            )
            messages.success(request, "Your message has been sent successfully! We will get back to you soon.")
            return redirect("contact")

    return render(request, "contact.html", {"active_section": "contact"})

