"""Seed a published light theme and dark theme so the demo's header renders.

Dev-only, demo-only: nothing here ships in the capy_shell package. Run it once
after `migrate` (see the demo section of the README). A theme is a single scheme,
so this seeds two — a light default and a dark default — which the shell's toggle
switches between. It does nothing if both defaults are already set, so it's safe to
run again.
"""

from capy_theme.models import Theme
from capy_theme.themes.active import default_themes
from capy_theme.themes.publishing import publish_and_activate
from django.core.management.base import BaseCommand

# (name, slug, daisyUI base) — the base sets each theme's scheme.
THEMES = [
    ("Capy Light", "capy-light-demo", "light"),
    ("Capy Dark", "capy-dark-demo", "dark"),
]


class Command(BaseCommand):
    help = "Create, publish and activate a demo light theme and dark theme (if not set)."

    def handle(self, *args, **options):
        defaults = default_themes()
        if defaults["light"] is not None and defaults["dark"] is not None:
            self.stdout.write("A light and a dark default theme are already set; nothing to do.")
            return
        for name, slug, base in THEMES:
            theme, _created = Theme.objects.get_or_create(
                slug=slug, defaults={"name": name, "base": base}
            )
            publish_and_activate(theme, note="Seeded by the demo's seed_theme command.")
            self.stdout.write(
                self.style.SUCCESS(f"Published and activated the demo {base} theme “{theme.name}”.")
            )
