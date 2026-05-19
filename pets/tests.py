from datetime import time

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from advisory.models import PetService, ServiceBooking
from records.models import MedicalRecord, Reminder, VaccinationRecord

from .models import HealthAssessment, MissingPet, Pet


User = get_user_model()


class PetDetailOverviewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="pet-owner",
            email="pet-owner@example.com",
            password="Strong-pass-2026",
        )
        self.pet = Pet.objects.create(
            owner=self.user,
            name="Juli",
            species="dog",
            breed="German Shepherd",
        )

    def test_pet_detail_shows_bookings_and_health_care_sections(self):
        today = timezone.localdate()
        service = PetService.objects.create(
            name="Healthy Paw Clinic",
            service_type="vet",
            city="Kochi",
        )
        ServiceBooking.objects.create(
            user=self.user,
            pet=self.pet,
            pet_service=service,
            booking_date=today,
            booking_time=time(10, 30),
            status="confirmed",
            notes="Annual checkup",
        )
        HealthAssessment.objects.create(
            pet=self.pet,
            overall_risk_level="medium",
            skin_infection_risk="medium",
            parasite_risk="low",
            fur_loss_risk="low",
            notes="AI Health Detection: Skin irritation (82% confidence).",
            symptom_details="Scratching near the neck",
            care_recommendations="Keep the affected area clean and book a vet visit.",
        )
        MedicalRecord.objects.create(
            pet=self.pet,
            visit_date=today,
            clinic_name="Healthy Paw Clinic",
            diagnosis="Skin irritation",
        )
        VaccinationRecord.objects.create(
            pet=self.pet,
            vaccine_name="Rabies",
            scheduled_date=today,
            status="scheduled",
        )
        Reminder.objects.create(
            pet=self.pet,
            title="Follow-up bath",
            reminder_type="grooming",
            due_date=today,
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse("pets:pet_detail", args=[self.pet.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["pet_bookings_count"], 1)
        self.assertEqual(response.context["health_assessments_count"], 1)
        self.assertEqual(response.context["medical_records_count"], 1)
        self.assertEqual(response.context["open_reminders_count"], 1)
        self.assertContains(response, "Care Overview")
        self.assertContains(response, "Healthy Paw Clinic")
        self.assertContains(response, "Medium Risk")
        self.assertContains(response, "Skin irritation")
        self.assertContains(response, "Rabies")
        self.assertContains(response, "Follow-up bath")


class MissingPetDashboardTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="Strong-pass-2026",
        )
        self.other_user = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="Strong-pass-2026",
        )
        self.staff_user = User.objects.create_user(
            username="staff",
            email="staff@example.com",
            password="Strong-pass-2026",
            is_staff=True,
        )
        self.pet = Pet.objects.create(owner=self.user, name="Milo", species="dog", breed="Beagle")
        self.report = MissingPet.objects.create(
            owner=self.user,
            pet=self.pet,
            pet_name="Milo",
            species="dog",
            breed="Beagle",
            description="Blue collar",
            last_seen_location="City Park",
            last_seen_date=timezone.now(),
            photo="missing_pets/milo.jpg",
            contact_phone="1234567890",
        )

    def test_owner_dashboard_shows_missing_report_actions(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("analytics:missing_pets_section"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Milo")
        self.assertContains(response, "Edit")
        self.assertContains(response, "Mark Found")

    def test_owner_can_update_missing_pet_report(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("pets:edit_missing_pet", args=[self.report.id]),
            {
                "pet": self.pet.id,
                "pet_name": "Milo Updated",
                "species": "dog",
                "breed": "Beagle Mix",
                "description": "Blue collar and white patch",
                "last_seen_location": "North Gate",
                "last_seen_date": timezone.localtime(self.report.last_seen_date).strftime("%Y-%m-%dT%H:%M"),
                "contact_phone": "9999999999",
            },
        )

        self.assertRedirects(response, reverse("analytics:missing_pets_section"))
        self.report.refresh_from_db()
        self.assertEqual(self.report.pet_name, "Milo Updated")
        self.assertEqual(self.report.last_seen_location, "North Gate")
        self.assertEqual(self.report.contact_phone, "9999999999")

    def test_other_user_cannot_edit_report(self):
        self.client.force_login(self.other_user)

        response = self.client.get(reverse("pets:edit_missing_pet", args=[self.report.id]))

        self.assertEqual(response.status_code, 404)

    def test_staff_custom_dashboard_shows_missing_pet_report(self):
        self.client.force_login(self.staff_user)

        response = self.client.get(reverse("analytics:ml_admin_dashboard") + "?panel=missing")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Missing Pet Reports")
        self.assertContains(response, "Milo")
        self.assertContains(response, "City Park")
