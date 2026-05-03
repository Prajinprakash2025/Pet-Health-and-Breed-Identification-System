from django.urls import path
from . import views
from pets import views as pet_views

app_name = "analytics"

urlpatterns = [
    path("", views.dashboard_view, name="dashboard"),
    path("analytics/", views.analytics_section_view, name="analytics_section"),
    path("health/", views.health_section_view, name="health_section"),
    path("records/", views.records_section_view, name="records_section"),
    path("my-pets/", views.my_pets_section_view, name="my_pets_section"),
    path("my-pets/add/", pet_views.pet_add_view, name="dashboard_pet_add"),
    path("advisory/", views.advisory_section_view, name="advisory_section"),
    path("medicines/", views.medicine_section_view, name="medicine_section"),
    path("services/", views.services_section_view, name="services_section"),
    path("ml-admin/", views.ml_admin_dashboard, name="ml_admin_dashboard"),
]
