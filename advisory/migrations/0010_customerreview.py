from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def seed_default_reviews(apps, schema_editor):
    CustomerReview = apps.get_model("advisory", "CustomerReview")
    CustomerReview.objects.create(
        name="Sarah Jenkins",
        role="Dog Owner",
        rating=5,
        message=(
            "PetCare AI completely changed how I look after my adopted mixed-breed dog. "
            "The health insights were spot on and helped me prepare for her veterinary visits."
        ),
        is_approved=True,
        show_on_home=True,
    )
    CustomerReview.objects.create(
        name="Mike Roberts",
        role="Shelter Volunteer",
        rating=4,
        message=(
            "As a volunteer at a shelter, the breed identification tool has been invaluable. "
            "We can provide much better information to potential adopters!"
        ),
        is_approved=True,
        show_on_home=True,
    )


def remove_default_reviews(apps, schema_editor):
    CustomerReview = apps.get_model("advisory", "CustomerReview")
    CustomerReview.objects.filter(name__in=["Sarah Jenkins", "Mike Roberts"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("advisory", "0009_contactmessage"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="CustomerReview",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("role", models.CharField(blank=True, help_text="Example: Dog Owner, Shelter Volunteer", max_length=120)),
                (
                    "rating",
                    models.PositiveSmallIntegerField(
                        choices=[
                            (1, "1 Star"),
                            (2, "2 Stars"),
                            (3, "3 Stars"),
                            (4, "4 Stars"),
                            (5, "5 Stars"),
                        ],
                        default=5,
                    ),
                ),
                ("message", models.TextField()),
                ("is_approved", models.BooleanField(default=False)),
                ("show_on_home", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="customer_reviews",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-show_on_home", "-is_approved", "-created_at"],
            },
        ),
        migrations.RunPython(seed_default_reviews, remove_default_reviews),
    ]
