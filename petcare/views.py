from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.urls import reverse

from advisory.forms import CustomerReviewForm
from advisory.models import CustomerReview
from pets.models import MissingPet, PetSighting


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
            review.is_approved = True
            review.show_on_home = True
            review.save()
            messages.success(request, "Thank you. Your review is now published.")
            return redirect(reverse("home") + "#reviews")
    else:
        review_form = CustomerReviewForm()

    home_reviews = list(CustomerReview.objects.filter(
        is_approved=True,
        show_on_home=True,
    ).order_by("-updated_at", "-created_at")[:8])
    featured_reviews = home_reviews[:4]
    additional_reviews = home_reviews[4:]
    review_count = CustomerReview.objects.filter(is_approved=True, show_on_home=True).count()
    latest_missing_reports = (
        MissingPet.objects.filter(is_found=False)
        .prefetch_related("sightings")
        .order_by("-created_at")[:2]
    )

    return render(
        request,
        "home.html",
        {
            "featured_reviews": featured_reviews,
            "additional_reviews": additional_reviews,
            "review_count": review_count,
            "review_form": review_form,
            "latest_missing_reports": latest_missing_reports,
            "open_missing_count": MissingPet.objects.filter(is_found=False).count(),
            "community_sighting_count": PetSighting.objects.count(),
        },
    )


def reviews(request):
    review_queryset = CustomerReview.objects.filter(
        is_approved=True,
        show_on_home=True,
    ).order_by("-updated_at", "-created_at")
    paginator = Paginator(review_queryset, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "reviews.html",
        {
            "page_obj": page_obj,
            "review_count": paginator.count,
        },
    )
