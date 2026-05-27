from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Avg
from django.shortcuts import redirect, render
from django.urls import reverse

from advisory.forms import CustomerReviewForm
from advisory.models import CustomerReview
from pets.models import MissingPet, Pet, PetSighting


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
    ).order_by("-updated_at", "-created_at")[:9])
    featured_reviews = home_reviews[:4]
    additional_reviews = home_reviews[4:]
    approved_reviews = CustomerReview.objects.filter(is_approved=True, show_on_home=True)
    review_count = approved_reviews.count()
    average_rating = approved_reviews.aggregate(value=Avg("rating"))["value"] or 5
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
            "average_rating": average_rating,
            "pet_count": Pet.objects.count(),
            "review_form": review_form,
            "latest_missing_reports": latest_missing_reports,
            "open_missing_count": MissingPet.objects.filter(is_found=False).count(),
            "community_sighting_count": PetSighting.objects.count(),
            "user_pets": Pet.objects.filter(owner=request.user) if request.user.is_authenticated else None,
        },
    )



def reviews(request):
    review_queryset = CustomerReview.objects.filter(
        is_approved=True,
        show_on_home=True,
    ).order_by("-updated_at", "-created_at")
    paginator = Paginator(review_queryset, 12)
    page_obj = paginator.get_page(request.GET.get("page"))
    average_rating = review_queryset.aggregate(value=Avg("rating"))["value"] or 5

    return render(
        request,
        "reviews.html",
        {
            "page_obj": page_obj,
            "review_count": paginator.count,
            "average_rating": average_rating,
            "pet_count": Pet.objects.count(),
        },
    )
