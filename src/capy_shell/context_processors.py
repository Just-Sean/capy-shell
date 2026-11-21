"""Make the shell's config available to templates as `shell`.

A project adds "capy_shell.context_processors.shell" to its template
context_processors so the shell base template can read every CAPY_SHELL_* setting:
the content container's width and padding, the brand link, and which chrome regions
are shown, whether they stick, and how wide they are.
"""

from . import conf

PREFIX = "CAPY_SHELL_"


THEME_COOKIE = "capy_shell_theme"


def shell(request):
    # Every CAPY_SHELL_* setting, keyed by its name without the prefix and
    # lowercased (CAPY_SHELL_SIDEBAR_WIDTH -> sidebar_width), so conf.DEFAULTS stays
    # the single list of the shell's settings.
    data = {name.removeprefix(PREFIX).lower(): conf.get(name) for name in conf.DEFAULTS}
    # The visitor's chosen theme (its slug), remembered by the theme picker; "default"
    # means the admin's default theme. The templates pass it to capy-theme's
    # {% theme_assets %} to render the chosen theme's stylesheet and logo.
    data["theme_slug"] = request.COOKIES.get(THEME_COOKIE, "default") if request else "default"
    return {"shell": data}
