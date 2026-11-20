from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    # Demo-only pages so the nav navigates and the active item updates.
    path(
        "settings/",
        TemplateView.as_view(template_name="demo_page.html", extra_context={"title": "Settings"}),
        name="demo_settings",
    ),
    path(
        "profile/",
        TemplateView.as_view(template_name="demo_page.html", extra_context={"title": "Profile"}),
        name="demo_profile",
    ),
    path("admin/", admin.site.urls),
    path("theme/", include("capy_theme.urls")),
    # Serves uploaded files (like theme logos) from demo/media/ while DEBUG is on.
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
]
