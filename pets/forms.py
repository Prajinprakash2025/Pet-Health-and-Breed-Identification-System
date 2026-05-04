from django import forms

from .models import Pet, MissingPet, PetSighting


class PetForm(forms.ModelForm):
    class Meta:
        model = Pet
        fields = [
            "name",
            "species",
            "breed",
            "date_of_birth",
            "weight_kg",
            "image",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "species": forms.Select(attrs={"class": "form-control"}),
            "breed": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Optional – AI will fill this after prediction",
                }
            ),
            "date_of_birth": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "weight_kg": forms.NumberInput(attrs={"class": "form-control"}),
            "image": forms.FileInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make it very clear that breed is optional
        if "breed" in self.fields:
            self.fields["breed"].required = False
            self.fields["breed"].label = "Breed (optional)"


class MissingPetForm(forms.ModelForm):
    class Meta:
        model = MissingPet
        fields = [
            "pet", "pet_name", "species", "breed", 
            "last_seen_location", "last_seen_lat", "last_seen_lng", "last_seen_date", 
            "photo", "contact_phone", "description"
        ]
        widgets = {
            "pet_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Pet's name"}),
            "species": forms.Select(attrs={"class": "form-control"}),
            "breed": forms.TextInput(attrs={"class": "form-control", "placeholder": "Breed (if known)"}),
            "last_seen_location": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. City Park, near North Gate"}),
            "last_seen_lat": forms.HiddenInput(),
            "last_seen_lng": forms.HiddenInput(),
            "last_seen_date": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "photo": forms.FileInput(attrs={"class": "form-control"}),
            "contact_phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "Your phone number"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Any distinctive marks, collar color, etc."}),
            "pet": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields["pet"].queryset = Pet.objects.filter(owner=user)
        self.fields["pet"].required = False
        self.fields["pet"].label = "Select from your pets (optional)"


class PetSightingForm(forms.ModelForm):
    class Meta:
        model = PetSighting
        fields = ["sighting_location", "sighting_date", "photo", "contact_info", "description"]
        widgets = {
            "sighting_location": forms.TextInput(attrs={"class": "form-control", "placeholder": "Where did you see the pet?"}),
            "sighting_date": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "photo": forms.FileInput(attrs={"class": "form-control"}),
            "contact_info": forms.TextInput(attrs={"class": "form-control", "placeholder": "Your phone or email"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Behavior, direction of travel, etc."}),
        }
