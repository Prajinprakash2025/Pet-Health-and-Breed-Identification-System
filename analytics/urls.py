from django.urls import path
from . import views

app_name = "analytics"

urlpatterns = [
    path("", views.dashboard_view, name="dashboard"),
    path("analytics/", views.analytics_section_view, name="analytics_section"),
    path("health/", views.health_section_view, name="health_section"),
    path("records/", views.records_section_view, name="records_section"),
    path("my-pets/", views.my_pets_section_view, name="my_pets_section"),
    path("ml-admin/", views.ml_admin_dashboard, name="ml_admin_dashboard"),
]
