from django.urls import path

from . import views


app_name = "records"

urlpatterns = [
    path("", views.records_home, name="records_home"),
    path("vaccinations/add/", views.add_vaccination_record, name="add_vaccination"),
    path("medical/add/", views.add_medical_record, name="add_medical"),
    path("reminders/", views.reminders_view, name="reminders"),
    path("reminders/<int:reminder_id>/complete/", views.complete_reminder, name="complete_reminder"),
    path("reminders/<int:reminder_id>/delete/", views.delete_reminder, name="delete_reminder"),
]
