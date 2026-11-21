"""A no-op stand-in for capy-theme's template tags.

The shell's templates load `capy_theme` for the theme's exposed data (the brand/logo),
but the module's own test project doesn't install capy-theme (and CI doesn't either).
Registering this as the `capy_theme` template library (see tests/settings.py) lets the
shell's templates render in the tests without it — with no theme, so the brand falls
back to nothing.
"""

from django import template

register = template.Library()


@register.simple_tag
def theme_artifacts():
    """Stand-in for capy-theme's data tag: no theme is installed in the tests."""
    return None
