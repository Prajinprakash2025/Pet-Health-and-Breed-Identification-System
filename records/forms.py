from django import forms

from pets.models import Pet

from .models import MedicalRecord, Reminder, VaccinationRecord


class OwnerPetFormMixin:
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None and "pet" in self.fields:
            self.fields["pet"].queryset = Pet.objects.filter(owner=user).order_by("name")


class VaccinationRecordForm(OwnerPetFormMixin, forms.ModelForm):
    class Meta:
        model = VaccinationRecord
        fields = (
            "pet",
            "vaccine_name",
            "scheduled_date",
            "administered_date",
            "status",
            "vet_name",
            "notes",
        )
        widgets = {
            "pet": forms.Select(attrs={"class": "form-control"}),
            "vaccine_name": forms.TextInput(attrs={"class": "form-control"}),
            "scheduled_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "administered_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-control"}),
            "vet_name": forms.TextInput(attrs={"class": "form-control"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class MedicalRecordForm(OwnerPetFormMixin, forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = (
            "pet",
            "visit_date",
            "clinic_name",
            "diagnosis",
            "treatment",
            "prescription",
            "follow_up_date",
        )
        widgets = {
            "pet": forms.Select(attrs={"class": "form-control"}),
            "visit_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "clinic_name": forms.TextInput(attrs={"class": "form-control"}),
            "diagnosis": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "treatment": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "prescription": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "follow_up_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        }


class ReminderForm(OwnerPetFormMixin, forms.ModelForm):
    class Meta:
        model = Reminder
        fields = ("pet", "title", "reminder_type", "due_date", "notes")
        widgets = {
            "pet": forms.Select(attrs={"class": "form-control"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "reminder_type": forms.Select(attrs={"class": "form-control"}),
            "due_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
