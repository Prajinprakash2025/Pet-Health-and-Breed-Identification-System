from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse

from advisory.forms import CustomerReviewForm
from advisory.models import CustomerReview


def home(request):
    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.error(request, "Please sign in to share your review.")
            return redirect("accounts:login")

        review_form = CustomerReviewForm(request.POST)
        if review_form.is_valid():
            review = review_form.save(commit=False)
            review.user = request.user
            review.name = (
                request.user.get_full_name()
                or request.user.username
                or request.user.email
                or "PetCare User"
            )
            review.save()
            messages.success(request, "Thank you. Your review was sent to admin for approval.")
            return redirect(reverse("home") + "#reviews")
    else:
        review_form = CustomerReviewForm()

    featured_reviews = CustomerReview.objects.filter(
        is_approved=True,
        show_on_home=True,
    ).order_by("-updated_at", "-created_at")[:4]

    return render(
        request,
        "home.html",
        {
            "featured_reviews": featured_reviews,
            "review_form": review_form,
        },
    )
