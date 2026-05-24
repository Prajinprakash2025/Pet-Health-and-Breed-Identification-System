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

    def test_logged_in_user_review_publishes_directly(self):
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
        self.assertTrue(review.is_approved)
        self.assertTrue(review.show_on_home)

        response = self.client.get(reverse("home"))
        self.assertContains(response, "PetCare AI helped me understand my pet health checks clearly.")

    def test_admin_can_hide_and_reply_to_review(self):
        review = CustomerReview.objects.create(
            user=self.user,
            name="Prajin Prakash",
            role="Dog Owner",
            rating=5,
            message="The dashboard made bookings and health details easy to understand.",
            is_approved=True,
            show_on_home=True,
        )
        self.client.force_login(self.staff_user)

        response = self.client.post(
            reverse("analytics:ml_admin_dashboard"),
            {
                "reply_review_id": review.id,
                "review_reply": "Thank you for sharing your experience.",
            },
        )

        self.assertRedirects(response, reverse("analytics:ml_admin_dashboard") + "?panel=reviews")
        review.refresh_from_db()
        self.assertEqual(review.admin_reply, "Thank you for sharing your experience.")
        self.assertTrue(review.is_approved)
        self.assertTrue(review.show_on_home)

        response = self.client.get(reverse("home"))
        self.assertContains(response, "Prajin Prakash")
        self.assertContains(response, "The dashboard made bookings and health details easy to understand.")
        self.assertContains(response, "Thank you for sharing your experience.")

        response = self.client.post(
            reverse("analytics:ml_admin_dashboard"),
            {"hide_review_id": review.id},
        )

        self.assertRedirects(response, reverse("analytics:ml_admin_dashboard") + "?panel=reviews")
        review.refresh_from_db()
        self.assertFalse(review.show_on_home)

    def test_home_page_limits_visible_reviews(self):
        existing_count = CustomerReview.objects.filter(is_approved=True, show_on_home=True).count()
        for index in range(6):
            CustomerReview.objects.create(
                name=f"Reviewer {index}",
                role="Pet Owner",
                rating=5,
                message=f"Visible review {index}",
                is_approved=True,
                show_on_home=True,
            )

        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["featured_reviews"]), 4)
        self.assertEqual(response.context["review_count"], existing_count + 6)
        self.assertContains(response, f"Showing the latest 4 of {existing_count + 6}")
        self.assertContains(response, reverse("reviews"))

    def test_reviews_page_shows_all_published_reviews_with_pagination(self):
        for index in range(13):
            CustomerReview.objects.create(
                name=f"Full Reviewer {index}",
                role="Pet Owner",
                rating=5,
                message=f"Full review message {index}",
                is_approved=True,
                show_on_home=True,
            )

        response = self.client.get(reverse("reviews"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "All Pet Owner Reviews")
        self.assertContains(response, "Full review message 12")
        self.assertContains(response, "Next")

        response = self.client.get(reverse("reviews"), {"page": 2})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Full review message 0")
