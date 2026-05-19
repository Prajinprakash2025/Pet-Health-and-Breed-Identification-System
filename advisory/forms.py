from django import forms

from .models import CustomerReview


class CustomerReviewForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["rating"].initial = 5
        self.fields["rating"].choices = [
            (5, "5 Stars"),
            (4, "4 Stars"),
            (3, "3 Stars"),
            (2, "2 Stars"),
            (1, "1 Star"),
        ]

    class Meta:
        model = CustomerReview
        fields = ("role", "rating", "message")
        labels = {
            "role": "Your pet owner type",
            "rating": "Rating",
            "message": "Your review",
        }
        widgets = {
            "role": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Dog Owner, Cat Parent, Shelter Volunteer...",
                    "maxlength": "120",
                }
            ),
            "rating": forms.HiddenInput(attrs={"id": "reviewRatingInput"}),
            "message": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Share how PetCare AI helped you care for your pet...",
                }
            ),
        }

    def clean_message(self):
        message = self.cleaned_data["message"].strip()
        if len(message) < 15:
            raise forms.ValidationError("Please write at least 15 characters.")
        return message
