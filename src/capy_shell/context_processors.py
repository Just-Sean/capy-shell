"""Make the shell's config available to templates as `shell`.

A project adds "capy_shell.context_processors.shell" to its template
context_processors so the shell base template can read every CAPY_SHELL_* setting:
the content container's width and padding, the brand link, and which chrome regions
are shown, whether they stick, and how wide they are.
"""

from . import conf

PREFIX = "CAPY_SHELL_"

# The visitor's chosen theme for each scheme (a theme slug), remembered by the theme
# picker. A theme is a single scheme, so there's one pick per scheme: a light one and
# a dark one, which the light/dark toggle switches between. capy-theme stores nothing;
# the shell owns the choice.
LIGHT_COOKIE = "capy_shell_light_theme"
DARK_COOKIE = "capy_shell_dark_theme"


def shell(request):
    # Every CAPY_SHELL_* setting, keyed by its name without the prefix and
    # lowercased (CAPY_SHELL_SIDEBAR_WIDTH -> sidebar_width), so conf.DEFAULTS stays
    # the single list of the shell's settings.
    data = {name.removeprefix(PREFIX).lower(): conf.get(name) for name in conf.DEFAULTS}
    # The visitor's picked theme for each scheme (or "" for none, so the admin's
    # default for that scheme is used). The templates pass these to the theme_slots
    # tag, which resolves each slot against capy-theme's catalog.
    data["light_pick"] = request.COOKIES.get(LIGHT_COOKIE, "") if request else ""
    data["dark_pick"] = request.COOKIES.get(DARK_COOKIE, "") if request else ""
    return {"shell": data}
