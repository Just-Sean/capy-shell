"""A dev-only demo app that seeds a theme so the shell's header renders."""

from django.apps import AppConfig


class DemoThemeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "demo_theme"
