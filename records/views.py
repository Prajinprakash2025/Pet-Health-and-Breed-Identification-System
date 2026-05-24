import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import MedicalRecordForm, ReminderForm, VaccinationRecordForm
from .models import MedicalRecord, PushNotificationToken, Reminder, VaccinationRecord


def _user_pet_ids(user):
    return user.pets.values_list("id", flat=True)


def _create_reminder_from_vaccination(record):
    if record.status == "completed" or not record.scheduled_date:
        return
    Reminder.objects.get_or_create(
        pet=record.pet,
        reminder_type="vaccination",
        due_date=record.scheduled_date,
        title=f"Vaccination: {record.vaccine_name}",
        defaults={"notes": record.notes},
    )


def _create_reminder_from_follow_up(record):
    if not record.follow_up_date:
        return
    Reminder.objects.get_or_create(
        pet=record.pet,
        reminder_type="follow_up",
        due_date=record.follow_up_date,
        title=f"Follow-up visit: {record.clinic_name or record.pet.name}",
        defaults={"notes": record.treatment or record.diagnosis},
    )


@login_required
def records_home(request):
    pet_ids = _user_pet_ids(request.user)
    today = timezone.localdate()
    vaccinations = (
        VaccinationRecord.objects.filter(pet__in=pet_ids)
        .select_related("pet")
        .order_by("-scheduled_date", "-administered_date")
    )
    medical_records = (
        MedicalRecord.objects.filter(pet__in=pet_ids)
        .select_related("pet")
        .order_by("-visit_date")
    )
    reminders = (
        Reminder.objects.filter(pet__in=pet_ids)
        .select_related("pet")
        .order_by("is_completed", "due_date")
    )

    context = {
        "vaccinations": vaccinations,
        "medical_records": medical_records,
        "reminders": reminders[:8],
        "overdue_count": reminders.filter(is_completed=False, due_date__lt=today).count(),
        "upcoming_count": reminders.filter(is_completed=False, due_date__gte=today).count(),
    }
    return render(request, "records/records_home.html", context)


@login_required
def add_vaccination_record(request):
    if request.method == "POST":
        form = VaccinationRecordForm(request.POST, user=request.user)
        if form.is_valid():
            record = form.save()
            _create_reminder_from_vaccination(record)
            messages.success(request, "Vaccination record saved.")
            return redirect("analytics:records_section")
    else:
        form = VaccinationRecordForm(user=request.user)
    return render(
        request,
        "records/record_form.html",
        {
            "form": form,
            "title": "Add Vaccination Record",
            "submit_label": "Save Vaccination",
            "active_section": "records",
        },
    )


@login_required
def add_medical_record(request):
    if request.method == "POST":
        form = MedicalRecordForm(request.POST, user=request.user)
        if form.is_valid():
            record = form.save()
            _create_reminder_from_follow_up(record)
            messages.success(request, "Medical record saved.")
            return redirect("analytics:records_section")
    else:
        form = MedicalRecordForm(user=request.user)
    return render(
        request,
        "records/record_form.html",
        {
            "form": form,
            "title": "Add Medical Record",
            "submit_label": "Save Medical Record",
            "active_section": "records",
        },
    )


@login_required
def reminders_view(request):
    pet_ids = _user_pet_ids(request.user)
    if request.method == "POST":
        form = ReminderForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Reminder created.")
            return redirect("records:reminders")
    else:
        form = ReminderForm(user=request.user)

    reminders = (
        Reminder.objects.filter(pet__in=pet_ids)
        .select_related("pet")
        .order_by("is_completed", "due_date")
    )
    return render(
        request,
        "records/reminders.html",
        {"form": form, "reminders": reminders, "active_section": "reminders"},
    )


@require_POST
@login_required
def complete_reminder(request, reminder_id):
    reminder = get_object_or_404(Reminder, id=reminder_id, pet__owner=request.user)
    reminder.is_completed = True
    reminder.save(update_fields=["is_completed"])
    messages.success(request, "Reminder marked as completed.")
    return redirect("records:reminders")


@require_POST
@login_required
def delete_reminder(request, reminder_id):
    reminder = get_object_or_404(Reminder, id=reminder_id, pet__owner=request.user)
    reminder.delete()
    messages.success(request, "Reminder deleted.")
    return redirect("records:reminders")


@require_POST
@login_required
def save_push_token(request):
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "Invalid JSON payload."}, status=400)

    token = (payload.get("token") or "").strip()
    if not token:
        return JsonResponse({"ok": False, "error": "Token is required."}, status=400)

    PushNotificationToken.objects.update_or_create(
        token=token,
        defaults={"user": request.user, "is_active": True},
    )
    return JsonResponse({"ok": True})


def firebase_messaging_sw(request):
    firebase_config = {
        "apiKey": settings.FIREBASE_WEB_API_KEY,
        "authDomain": settings.FIREBASE_AUTH_DOMAIN,
        "projectId": settings.FIREBASE_PROJECT_ID,
        "storageBucket": settings.FIREBASE_STORAGE_BUCKET,
        "messagingSenderId": settings.FIREBASE_MESSAGING_SENDER_ID,
        "appId": settings.FIREBASE_APP_ID,
        "measurementId": settings.FIREBASE_MEASUREMENT_ID,
    }
    config_json = json.dumps(firebase_config)
    script = f"""
importScripts("https://www.gstatic.com/firebasejs/10.14.1/firebase-app-compat.js");
importScripts("https://www.gstatic.com/firebasejs/10.14.1/firebase-messaging-compat.js");

firebase.initializeApp({config_json});

const messaging = firebase.messaging();

messaging.onBackgroundMessage((payload) => {{
    const notification = payload.notification || {{}};
    const data = payload.data || {{}};
    const title = notification.title || "PetCare Notification";
    const options = {{
        body: notification.body || "You have a new PetCare update.",
        data: {{
            url: data.url || "/pets/notifications/",
        }},
    }};
    if (data.icon) {{
        options.icon = data.icon;
    }}
    self.registration.showNotification(title, options);
}});

self.addEventListener("notificationclick", (event) => {{
    event.notification.close();
    const url = event.notification.data && event.notification.data.url
        ? event.notification.data.url
        : "/pets/notifications/";
    event.waitUntil(clients.openWindow(url));
}});
"""
    return HttpResponse(script, content_type="application/javascript")
