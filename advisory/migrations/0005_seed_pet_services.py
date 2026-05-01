from django.db import migrations


def seed_pet_services(apps, schema_editor):
    PetService = apps.get_model("advisory", "PetService")
    VetDoctor = apps.get_model("advisory", "VetDoctor")

    services = [
        {
            "name": "Kochi Pet Wellness Clinic",
            "service_type": "vet",
            "city": "Kochi",
            "address": "MG Road, Ernakulam, Kochi",
            "phone": "+91 98765 43210",
            "email": "care@kochipheroes.example",
            "opening_hours": "Mon-Sat, 9:00 AM - 7:00 PM",
            "notes": "General checkups, vaccinations, skin care, and follow-up visits.",
        },
        {
            "name": "Happy Paws Grooming Studio",
            "service_type": "groomer",
            "city": "Kochi",
            "address": "Panampilly Nagar, Kochi",
            "phone": "+91 98765 43211",
            "opening_hours": "Daily, 10:00 AM - 6:00 PM",
            "notes": "Bathing, brushing, nail trimming, ear cleaning, and coat care.",
        },
        {
            "name": "Smart Tails Training Center",
            "service_type": "trainer",
            "city": "Kochi",
            "address": "Kakkanad, Kochi",
            "phone": "+91 98765 43212",
            "opening_hours": "Mon-Fri, 8:00 AM - 6:00 PM",
            "notes": "Basic obedience, leash training, puppy socialization, and behavior support.",
        },
        {
            "name": "Pet Stay Boarding Hub",
            "service_type": "boarding",
            "city": "Kochi",
            "address": "Vyttila, Kochi",
            "phone": "+91 98765 43213",
            "opening_hours": "24 hours",
            "notes": "Short-stay and overnight boarding with feeding and activity schedules.",
        },
        {
            "name": "CarePlus Pet Pharmacy",
            "service_type": "pharmacy",
            "city": "Kochi",
            "address": "Edappally, Kochi",
            "phone": "+91 98765 43214",
            "opening_hours": "Mon-Sun, 9:00 AM - 9:00 PM",
            "notes": "Pet medicines, supplements, parasite preventives, and prescription supplies.",
        },
    ]
    for item in services:
        PetService.objects.get_or_create(
            name=item["name"],
            service_type=item["service_type"],
            city=item["city"],
            defaults=item,
        )

    doctors = [
        {
            "name": "Anjali Menon",
            "specialization": "general",
            "phone": "+91 98765 43220",
            "email": "dr.anjali@example.com",
            "clinic_name": "Kochi Pet Wellness Clinic",
            "address": "MG Road, Ernakulam, Kochi",
            "experience_years": 8,
            "is_available": True,
        },
        {
            "name": "Rahul Nair",
            "specialization": "dermatology",
            "phone": "+91 98765 43221",
            "email": "dr.rahul@example.com",
            "clinic_name": "Skin & Coat Pet Care",
            "address": "Kadavanthra, Kochi",
            "experience_years": 6,
            "is_available": True,
        },
    ]
    for item in doctors:
        VetDoctor.objects.get_or_create(
            name=item["name"],
            clinic_name=item["clinic_name"],
            defaults=item,
        )


def remove_pet_services(apps, schema_editor):
    PetService = apps.get_model("advisory", "PetService")
    VetDoctor = apps.get_model("advisory", "VetDoctor")

    PetService.objects.filter(
        name__in=[
            "Kochi Pet Wellness Clinic",
            "Happy Paws Grooming Studio",
            "Smart Tails Training Center",
            "Pet Stay Boarding Hub",
            "CarePlus Pet Pharmacy",
        ]
    ).delete()
    VetDoctor.objects.filter(
        name__in=[
            "Anjali Menon",
            "Rahul Nair",
        ]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("advisory", "0004_seed_advisory_data"),
    ]

    operations = [
        migrations.RunPython(seed_pet_services, remove_pet_services),
    ]
