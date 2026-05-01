from django.urls import path

from . import views


app_name = "advisory"

urlpatterns = [
    path("", views.advisory_home, name="advisory_home"),
    path("medicines/", views.medicine_recommendations, name="medicine_recommendations"),
    path("services/", views.service_finder, name="service_finder"),
    path("book-service/", views.book_service, name="book_service"),
]
