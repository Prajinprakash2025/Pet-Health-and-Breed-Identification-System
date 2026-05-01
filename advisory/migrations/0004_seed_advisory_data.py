from django.db import migrations


def seed_advisory_data(apps, schema_editor):
    CareAdvisory = apps.get_model("advisory", "CareAdvisory")
    MedicineRecommendation = apps.get_model("advisory", "MedicineRecommendation")
    VaccinationScheduleTemplate = apps.get_model("advisory", "VaccinationScheduleTemplate")

    advisories = [
        {
            "species": "both",
            "category": "vaccination",
            "title": "Core vaccination planning",
            "short_summary": "Keep core vaccines current and record booster dates.",
            "recommendation": "Follow species-specific core vaccine schedules, keep proof of vaccination, and review boosters during annual wellness visits.",
            "when_to_apply": "Start during puppy or kitten care, then continue through adult and senior life.",
        },
        {
            "species": "both",
            "category": "diet",
            "title": "Balanced daily nutrition",
            "short_summary": "Match food portions to age, weight, activity level, and health status.",
            "recommendation": "Use complete pet food, avoid sudden diet changes, provide clean water, and monitor weight monthly. Ask a vet before using supplements or restrictive diets.",
            "when_to_apply": "Daily feeding and weight management.",
        },
        {
            "species": "both",
            "category": "grooming",
            "title": "Coat, nail, and ear grooming",
            "short_summary": "Routine grooming helps find skin, fur, nail, and ear problems early.",
            "recommendation": "Brush regularly, trim nails safely, clean visible ear dirt with pet-safe products, and stop if there is pain, bleeding, swelling, or strong odor.",
            "when_to_apply": "Weekly for most pets, more often for long-haired breeds.",
        },
        {
            "species": "both",
            "category": "hygiene",
            "title": "Home hygiene care",
            "short_summary": "Clean bowls, bedding, litter boxes, and play areas to lower infection risk.",
            "recommendation": "Wash food and water bowls daily, clean bedding often, keep litter boxes fresh, and disinfect shared spaces with pet-safe cleaners.",
            "when_to_apply": "Daily to weekly depending on the item.",
        },
        {
            "species": "both",
            "category": "parasite",
            "title": "Flea, tick, and worm prevention",
            "short_summary": "Parasite prevention should match species, body weight, age, and local risk.",
            "recommendation": "Use vet-approved flea, tick, and deworming prevention. Check the skin and coat after outdoor exposure and keep the living area clean.",
            "when_to_apply": "Year-round or seasonal based on local parasite risk.",
        },
        {
            "species": "both",
            "category": "treatment",
            "title": "When symptoms need treatment",
            "short_summary": "Treatment decisions should be based on symptoms, exam findings, and vet guidance.",
            "recommendation": "Seek veterinary help for wounds, repeated vomiting, breathing trouble, severe itching, eye discharge, sudden weakness, seizures, or symptoms lasting more than 24 hours.",
            "when_to_apply": "Any time symptoms are severe, unusual, or persistent.",
        },
    ]
    for item in advisories:
        CareAdvisory.objects.get_or_create(
            species=item["species"],
            category=item["category"],
            title=item["title"],
            defaults=item,
        )

    medicines = [
        {
            "species": "both",
            "condition_name": "Flea, tick, and mite prevention",
            "medicine_name": "Vet-approved parasite preventive",
            "dosage_guidance": "Select the product and dose by species, weight, age, and label instructions under veterinary guidance.",
            "administration_notes": "Topical, oral, or collar options may be used depending on the pet and local parasite risk.",
            "warnings": "Never use dog-only permethrin products on cats. Do not combine parasite products unless a vet approves it.",
        },
        {
            "species": "dog",
            "condition_name": "Allergic dermatitis",
            "medicine_name": "Antihistamine or anti-inflammatory medication",
            "dosage_guidance": "Use only when prescribed or approved by a veterinarian after checking weight, symptoms, and other medicines.",
            "administration_notes": "A vet may also recommend medicated shampoo, diet review, or flea control.",
            "warnings": "Human medicines can be unsafe for pets. Do not guess doses.",
        },
        {
            "species": "both",
            "condition_name": "Fungal skin infection",
            "medicine_name": "Antifungal shampoo or prescribed antifungal medicine",
            "dosage_guidance": "Use only with veterinary diagnosis and instructions. Treatment length varies by infection type and severity.",
            "administration_notes": "Keep affected areas dry and wash bedding regularly during treatment.",
            "warnings": "Some fungal infections spread to people and other animals. Isolate and handle carefully until cleared by a vet.",
        },
    ]
    for item in medicines:
        MedicineRecommendation.objects.get_or_create(
            species=item["species"],
            condition_name=item["condition_name"],
            medicine_name=item["medicine_name"],
            defaults=item,
        )

    vaccines = [
        ("dog", "DHPP", 6, 3, "Core puppy vaccine series."),
        ("dog", "Rabies", 12, 52, "Follow local legal requirements for rabies boosters."),
        ("dog", "Leptospirosis", 10, 52, "Recommended where exposure risk is present."),
        ("dog", "Bordetella", 8, 52, "Useful for boarding, grooming, and social dogs."),
        ("cat", "FVRCP", 6, 3, "Core kitten vaccine series."),
        ("cat", "Rabies", 12, 52, "Follow local legal requirements for rabies boosters."),
        ("cat", "FeLV", 8, 52, "Recommended for kittens and cats with outdoor exposure risk."),
    ]
    for species, vaccine_name, age, repeat, notes in vaccines:
        VaccinationScheduleTemplate.objects.get_or_create(
            species=species,
            vaccine_name=vaccine_name,
            recommended_age_weeks=age,
            defaults={"repeat_interval_weeks": repeat, "notes": notes},
        )


def remove_seed_advisory_data(apps, schema_editor):
    CareAdvisory = apps.get_model("advisory", "CareAdvisory")
    MedicineRecommendation = apps.get_model("advisory", "MedicineRecommendation")
    VaccinationScheduleTemplate = apps.get_model("advisory", "VaccinationScheduleTemplate")

    CareAdvisory.objects.filter(
        title__in=[
            "Core vaccination planning",
            "Balanced daily nutrition",
            "Coat, nail, and ear grooming",
            "Home hygiene care",
            "Flea, tick, and worm prevention",
            "When symptoms need treatment",
        ]
    ).delete()
    MedicineRecommendation.objects.filter(
        medicine_name__in=[
            "Vet-approved parasite preventive",
            "Antihistamine or anti-inflammatory medication",
            "Antifungal shampoo or prescribed antifungal medicine",
        ]
    ).delete()
    VaccinationScheduleTemplate.objects.filter(
        vaccine_name__in=["DHPP", "Rabies", "Leptospirosis", "Bordetella", "FVRCP", "FeLV"]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("advisory", "0003_careadvisory_petservice_medicinerecommendation"),
    ]

    operations = [
        migrations.RunPython(seed_advisory_data, remove_seed_advisory_data),
    ]
