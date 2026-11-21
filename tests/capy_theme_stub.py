"""A stand-in for capy-theme's template tags.

The shell's templates load `capy_theme` for the theme's exposed data (the brand/logo, the
stylesheet, the theme picker), but the module's own test project doesn't install
capy-theme (and CI doesn't either). Registering this as the `capy_theme` template library
(see tests/settings.py) lets the shell's templates render in the tests without it, with
two stand-in themes so the picker renders.
"""

from django import template

register = template.Library()

# Two stand-in themes, so the picker (shown when there's more than one) renders in tests.
_THEMES = [
    {"slug": "ocean", "name": "Ocean", "default": True},
    {"slug": "forest", "name": "Forest", "default": False},
]


@register.simple_tag
def theme_artifacts():
    """Stand-in for capy-theme's default-theme data tag: no theme is installed here."""
    return None


@register.simple_tag
def theme_catalog():
    """Stand-in for the catalog tag: the available themes (the real one reads capy-theme)."""
    return _THEMES


@register.simple_tag
def theme_assets(slug):
    """Stand-in for one theme's assets by slug; None for an unknown theme."""
    if slug == "default" or any(theme["slug"] == slug for theme in _THEMES):
        return {
            "stylesheet_url": "/theme/stub.css",
            "logos": {"logo_main": {"light": None, "dark": None}},
            "branding": {"site_name": "Stub theme"},
        }
    return None
