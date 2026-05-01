from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include(("accounts.urls", "accounts"), namespace="accounts")),
    path("advisory/", include("advisory.urls", namespace="advisory")),
    path("pets/", include("pets.urls", namespace="pets")),
    path("records/", include("records.urls", namespace="records")),
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
        TemplateView.as_view(template_name="contact.html"),
        name="contact",
    ),
    path("dashboard/", include("analytics.urls", namespace="analytics")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
