"""URLs for the test project."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("shell/", include("capy_shell.urls")),
]
