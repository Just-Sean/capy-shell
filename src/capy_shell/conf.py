"""The settings a project can set (CAPY_SHELL_*) and their defaults.

Every CAPY_SHELL_* setting is read through get(), so this is the one place that
lists them. The README's Settings table lists the same ones.

capy-shell owns page *structure and geometry* (which regions exist, the content
container's width and padding); the *look* (colors, type, spacing scale) comes
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
    # The chrome regions around the content, and how each behaves. The header is
    # always present (it holds the brand, the mode toggle and, on small screens,
    # the burger that opens the sidebar drawer); the sidebar, aside and footer are
    # present only when turned on. "Sticky" keeps a region in view as the page
    # scrolls; widths are Tailwind classes. The regions are empty until something
    # fills their blocks (nav content arrives in a later feature). On small screens
    # the sidebar collapses into a responsive burger drawer (see base.html /
    # shell.css).
    "CAPY_SHELL_HEADER_STICKY": True,
    "CAPY_SHELL_SIDEBAR": True,
    "CAPY_SHELL_SIDEBAR_WIDTH": "w-64",
    "CAPY_SHELL_SIDEBAR_STICKY": True,
    "CAPY_SHELL_ASIDE": False,
    "CAPY_SHELL_ASIDE_WIDTH": "w-64",
    "CAPY_SHELL_ASIDE_STICKY": True,
    "CAPY_SHELL_FOOTER": False,
    # Extra directories of SVG icons, searched (in order) before the icons that ship
    # with capy-shell, so a project can add its own or override a built-in by name.
    # Each entry is a path to a folder of "<name>.svg" files. See the {% icon %} tag
    # (templatetags/capy_icons.py) and the README.
    "CAPY_SHELL_ICON_DIRS": [],
}


def get(name):
    """The project's value for a CAPY_SHELL_* setting, or its default."""
    return getattr(settings, name, DEFAULTS[name])
