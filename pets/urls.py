from django.urls import path

from . import views


app_name = "pets"

urlpatterns = [
    path("", views.pet_list_view, name="pet_list"),
    path("add/", views.pet_add_view, name="pet_add"),
    path("<int:pet_id>/", views.pet_detail_view, name="pet_detail"),
    path("<int:pet_id>/edit/", views.pet_edit_view, name="pet_edit"),
    path("<int:pet_id>/identify/", views.breed_identify_view, name="breed_identify"),
    path("<int:pet_id>/predict/", views.run_breed_prediction_view, name="run_breed_prediction"),
    path("<int:pet_id>/health-scan/", views.health_scan_view, name="health_scan"),
    path("<int:pet_id>/run-health-scan/", views.run_health_prediction_view, name="run_health_prediction"),
    
    # Missing Pets
    path("missing/", views.missing_pets_list_view, name="missing_pets_list"),
    path("missing/report/", views.report_missing_view, name="report_missing"),
    path("missing/<int:report_id>/", views.missing_pet_detail_view, name="missing_pet_detail"),
]
