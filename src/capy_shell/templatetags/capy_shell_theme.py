"""capy-shell's own theme tags: which theme fills the light slot and the dark slot.

capy-shell asks capy-theme for the catalog ({% theme_catalog %}); these tags work out,
for each scheme, which theme fills that slot — the visitor's pick if it's a theme of that
scheme in the catalog, otherwise the admin's default theme for that scheme. They operate
only on the plain catalog data capy-theme exposes; capy-shell never imports capy-theme.
"""

from django import template

register = template.Library()


@register.simple_tag
def scheme_themes(catalog, scheme):
    """The catalog entries for one scheme ("light" or "dark"), in the catalog's order."""
    return [entry for entry in (catalog or []) if entry.get("scheme") == scheme]


@register.simple_tag
def theme_slots(catalog, light_pick="", dark_pick=""):
    """Return ``{"light": entry or None, "dark": entry or None}`` from the catalog.

    ``catalog`` is the list from capy-theme's {% theme_catalog %}. For each scheme the slot
    is the entry whose slug matches the visitor's pick, else the catalog's default entry
    for that scheme, else None (so the host's own daisyUI default applies for that slot).
    """
    catalog = catalog or []
    return {
        "light": _slot(catalog, "light", light_pick),
        "dark": _slot(catalog, "dark", dark_pick),
    }


def _slot(catalog, scheme, pick):
    entries = scheme_themes(catalog, scheme)
    if pick:
        for entry in entries:
            if entry.get("slug") == pick:
                return entry
    return next((entry for entry in entries if entry.get("default")), None)
