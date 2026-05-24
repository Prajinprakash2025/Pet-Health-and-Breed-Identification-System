from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from advisory.models import CareAdvisory, VaccinationScheduleTemplate
from pets.models import HealthAssessment, Pet


User = get_user_model()


class AdminDashboardChartTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="Strong-pass-2026",
            is_staff=True,
        )
        self.client.force_login(self.staff)

    def test_admin_dashboard_renders_chart_canvases_when_data_exists(self):
        pet = Pet.objects.create(owner=self.staff, name="Milo", species="dog")
        HealthAssessment.objects.create(pet=pet, overall_risk_level="low")

        response = self.client.get(reverse("analytics:ml_admin_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="speciesChart"')
        self.assertContains(response, 'id="healthChart"')
        content = response.content.decode()
        self.assertLess(
            content.index("</script>\n<!--"),
            content.index('id="statusUpdateModal"'),
        )

    def test_admin_dashboard_shows_empty_chart_messages_without_data(self):
        response = self.client.get(reverse("analytics:ml_admin_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No pet species data yet.")
        self.assertContains(response, "No health scan data yet.")

    def test_admin_sidebar_links_target_panels(self):
        response = self.client.get(reverse("analytics:ml_admin_dashboard") + "?panel=users")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-panel="users" href="?panel=users"')
        self.assertContains(response, 'data-panel="bookings" href="?panel=bookings"')
        self.assertContains(response, 'data-panel="advisory" href="?panel=advisory"')
        self.assertContains(response, "function activatePanel(panel, updateUrl = true)")
        self.assertContains(response, "aria-current")

    def test_admin_can_add_veterinary_advisory_content(self):
        response = self.client.post(
            reverse("analytics:ml_admin_dashboard"),
            {
                "add_advisory": "1",
                "advisory_species": "both",
                "advisory_category": "diet",
                "advisory_title": "Hydration check",
                "advisory_summary": "Keep clean water available.",
                "advisory_recommendation": "Refresh drinking water daily and watch for reduced intake.",
                "advisory_when": "Daily",
                "advisory_active": "on",
            },
        )

        self.assertRedirects(response, reverse("analytics:ml_admin_dashboard") + "?panel=advisory")
        self.assertTrue(CareAdvisory.objects.filter(title="Hydration check", is_active=True).exists())

    def test_admin_can_add_vaccination_template(self):
        response = self.client.post(
            reverse("analytics:ml_admin_dashboard"),
            {
                "add_vaccine_template": "1",
                "vaccine_species": "dog",
                "vaccine_name": "Test Vaccine",
                "vaccine_age": "12",
                "vaccine_repeat": "52",
                "vaccine_notes": "Annual booster.",
            },
        )

        self.assertRedirects(response, reverse("analytics:ml_admin_dashboard") + "?panel=advisory")
        self.assertTrue(
            VaccinationScheduleTemplate.objects.filter(
                species="dog",
                vaccine_name="Test Vaccine",
                recommended_age_weeks=12,
                repeat_interval_weeks=52,
            ).exists()
        )
