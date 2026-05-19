from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import CustomerReview


User = get_user_model()


class CustomerReviewWorkflowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="reviewer",
            email="reviewer@example.com",
            password="Strong-pass-2026",
            first_name="Prajin",
            last_name="Prakash",
        )
        self.staff_user = User.objects.create_user(
            username="staff",
            email="staff@example.com",
            password="Strong-pass-2026",
            is_staff=True,
        )

    def test_logged_in_user_can_submit_review_for_admin_approval(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("home"),
            {
                "role": "Dog Owner",
                "rating": 5,
                "message": "PetCare AI helped me understand my pet health checks clearly.",
            },
        )

        self.assertRedirects(response, reverse("home") + "#reviews")
        review = CustomerReview.objects.get(message__icontains="health checks clearly")
        self.assertEqual(review.user, self.user)
        self.assertEqual(review.name, "Prajin Prakash")
        self.assertFalse(review.is_approved)
        self.assertFalse(review.show_on_home)

        response = self.client.get(reverse("home"))
        self.assertNotContains(response, "PetCare AI helped me understand my pet health checks clearly.")

    def test_admin_can_publish_review_to_home_page(self):
        review = CustomerReview.objects.create(
            user=self.user,
            name="Prajin Prakash",
            role="Dog Owner",
            rating=5,
            message="The dashboard made bookings and health details easy to understand.",
        )
        self.client.force_login(self.staff_user)

        response = self.client.post(
            reverse("analytics:ml_admin_dashboard"),
            {"publish_review_id": review.id},
        )

        self.assertRedirects(response, reverse("analytics:ml_admin_dashboard") + "?panel=reviews")
        review.refresh_from_db()
        self.assertTrue(review.is_approved)
        self.assertTrue(review.show_on_home)

        response = self.client.get(reverse("home"))
        self.assertContains(response, "Prajin Prakash")
        self.assertContains(response, "The dashboard made bookings and health details easy to understand.")
