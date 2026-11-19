"""Make the shell's config available to templates as `shell`.

A project adds "capy_shell.context_processors.shell" to its template
context_processors so the shell base template can read every CAPY_SHELL_* setting:
the content container's width and padding, the brand link, and which chrome regions
are shown, whether they stick, and how wide they are.
"""

from . import conf

PREFIX = "CAPY_SHELL_"


def shell(request):
    # Every CAPY_SHELL_* setting, keyed by its name without the prefix and
    # lowercased (CAPY_SHELL_SIDEBAR_WIDTH -> sidebar_width), so conf.DEFAULTS stays
    # the single list of the shell's settings.
    return {"shell": {name.removeprefix(PREFIX).lower(): conf.get(name) for name in conf.DEFAULTS}}
