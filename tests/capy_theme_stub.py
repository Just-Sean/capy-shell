"""A no-op stand-in for capy-theme's template tags.

The shell's templates load `capy_theme` for the logo and mode toggle, but the
module's own test project doesn't install capy-theme (and CI doesn't either).
Registering this as the `capy_theme` template library (see tests/settings.py) lets
the shell's templates render in the tests without it.
"""

from django import template

register = template.Library()


@register.simple_tag
def theme_logo():
    return ""


@register.simple_tag
def theme_mode_toggle():
    return ""
