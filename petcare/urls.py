from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from advisory.views import contact
from django.conf import settings
from django.conf.urls.static import static
from records.views import firebase_messaging_sw


urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include(("accounts.urls", "accounts"), namespace="accounts")),
    path("advisory/", include("advisory.urls", namespace="advisory")),
    path("pets/", include("pets.urls", namespace="pets")),
    path("records/", include("records.urls", namespace="records")),
    path("firebase-messaging-sw.js", firebase_messaging_sw, name="firebase_messaging_sw"),
    path(
        "",
        TemplateView.as_view(template_name="home.html"),
        name="home",
    ),
    path(
        "about/",
        TemplateView.as_view(template_name="about.html"),
        name="about",
    ),
    path(
        "contact/",
        contact,
        name="contact",
    ),
    path(
        "terms/",
        TemplateView.as_view(template_name="terms.html"),
        name="terms",
    ),
    path(
        "privacy/",
        TemplateView.as_view(template_name="privacy.html"),
        name="privacy",
    ),
    path("dashboard/", include("analytics.urls", namespace="analytics")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
