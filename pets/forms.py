from django import forms

from .models import Pet


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
