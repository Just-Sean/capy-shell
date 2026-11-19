"""Seed a published light/dark theme so the demo's header renders.

Dev-only, demo-only: nothing here ships in the capy_shell package. Run it once
after `migrate` (see the demo section of the README). It does nothing if a theme
is already active, so it's safe to run again.
"""

from capy_theme.models import Theme
from capy_theme.themes.active import get_active_theme
from capy_theme.themes.publishing import publish_and_activate
from django.core.management.base import BaseCommand

THEME_NAME = "Capy Demo"
THEME_SLUG = "capy-demo"


class Command(BaseCommand):
    help = "Create, publish and activate a demo light/dark theme (if none is active)."

    def handle(self, *args, **options):
        if get_active_theme() is not None:
            self.stdout.write("A theme is already active; nothing to do.")
            return

        theme, _created = Theme.objects.get_or_create(
            slug=THEME_SLUG,
            defaults={"name": THEME_NAME, "light_base": "light", "dark_base": "dark"},
        )
        publish_and_activate(theme, note="Seeded by the demo's seed_theme command.")
        self.stdout.write(
            self.style.SUCCESS(f"Published and activated the demo theme “{theme.name}”.")
        )
