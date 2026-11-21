"""A stand-in for capy-theme's template tags.

The shell's templates load `capy_theme` for the theme's exposed data (the catalog, each
theme's assets, the brand/logo), but the module's own test project doesn't install
capy-theme (and CI doesn't either). Registering this as the `capy_theme` template library
(see tests/settings.py) lets the shell's templates render in the tests without it, with a
few stand-in themes — two light and two dark, with one default each — so the picker and
the slot resolution render.
"""

from django import template

register = template.Library()

# A few stand-in themes, keyed by slug. The real catalog comes from capy-theme.
_THEMES = {
    "dawn": {"name": "Dawn", "scheme": "light", "default": True},
    "paper": {"name": "Paper", "scheme": "light", "default": False},
    "midnight": {"name": "Midnight", "scheme": "dark", "default": True},
    "ink": {"name": "Ink", "scheme": "dark", "default": False},
}


def _entry(slug, theme):
    return {
        "slug": slug,
        "name": theme["name"],
        "scheme": theme["scheme"],
        "default": theme["default"],
        "swatch": "#4f46e5" if theme["scheme"] == "light" else "#a5b4fc",
        "background": "#ffffff" if theme["scheme"] == "light" else "#111827",
        "assets_url": f"/theme/themes/{slug}.json",
        "stylesheet_url": f"/theme/{slug}.css",
    }


@register.simple_tag
def theme_catalog():
    """Stand-in for the catalog tag: the available themes (the real one reads capy-theme)."""
    return [_entry(slug, theme) for slug, theme in _THEMES.items()]


@register.simple_tag
def theme_assets(slug):
    """Stand-in for one theme's assets by slug; None for an unknown theme."""
    if slug == "default":
        slug = "dawn"
    theme = _THEMES.get(slug)
    if theme is None:
        return None
    return {
        "stylesheet_url": f"/theme/{slug}.css",
        "logos": {"logo_main": None},
        "branding": {"site_name": theme["name"]},
    }


@register.simple_tag
def theme_artifacts():
    """Stand-in for capy-theme's primary-theme data tag: the default light theme's assets."""
    return theme_assets("dawn")
