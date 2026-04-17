from django.urls import path

from . import views


app_name = "pets"

urlpatterns = [
    path("", views.pet_list_view, name="pet_list"),
    path("add/", views.pet_add_view, name="pet_add"),
    path("<int:pet_id>/", views.pet_detail_view, name="pet_detail"),
    path("<int:pet_id>/edit/", views.pet_edit_view, name="pet_edit"),
    path("<int:pet_id>/predict/", views.run_breed_prediction_view, name="run_breed_prediction"),
    path("<int:pet_id>/health-scan/", views.health_scan_view, name="health_scan"),
    path("<int:pet_id>/run-health-scan/", views.run_health_prediction_view, name="run_health_prediction"),
]
