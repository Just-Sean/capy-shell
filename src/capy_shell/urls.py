"""The shell's URLs.

A project includes them in its urls.py, e.g.
``path("shell/", include("capy_shell.urls"))`` — the theme picker links here.
"""

from django.urls import path

from . import views

app_name = "capy_shell"

urlpatterns = [
    path("set-theme/<slug:slug>/", views.set_theme, name="set_theme"),
]
