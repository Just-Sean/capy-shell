"""The settings a project can set (CAPY_SHELL_*) and their defaults.

Every CAPY_SHELL_* setting is read through get(), so this is the one place that
lists them. The README's Settings table lists the same ones.

capy-shell owns page *structure and geometry* (which regions exist, the content
container's width and padding); the *look* (colours, type, spacing scale) comes
from capy-theme's daisyUI tokens, so there are deliberately few style settings here.
"""

from django.conf import settings

DEFAULTS = {
    # Tailwind classes for the content container that pages render inside. The
    # max-width keeps lines readable on wide screens; a page needing full width
    # overrides the container in its own template.
    "CAPY_SHELL_CONTENT_MAX_WIDTH": "max-w-7xl",
    "CAPY_SHELL_CONTENT_PADDING": "px-4 py-6",
    # Where the header's brand/logo links (a path or a name the project resolves).
    "CAPY_SHELL_HOME_URL": "/",
}


def get(name):
    """The project's value for a CAPY_SHELL_* setting, or its default."""
    return getattr(settings, name, DEFAULTS[name])
