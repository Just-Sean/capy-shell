"""The capy-shell nav system.

Modules **declare** nav as plain data in their own ``nav.py`` (a ``NAV`` list of dicts
— see the README); they never import capy-shell. capy-shell **collects** and merges it.
``get_nav(request)`` is the stable interface the app-shell renders through — so a
different shell can read the same declarations.

``get_nav`` returns render-ready groups for the request: filtered by the user's
permissions, each link's URL resolved and the active item marked. Admin-editable DB
overrides build on it in a later feature; the signature stays the same.
"""

from __future__ import annotations

from .collect import collect, merge, sections
from .render import build_nav
from .schema import (
    DEFAULT_ORDER,
    NavError,
    NavGroup,
    NavItem,
    NavLink,
    NavSection,
    validate,
)

__all__ = [
    "DEFAULT_ORDER",
    "NavError",
    "NavGroup",
    "NavItem",
    "NavLink",
    "NavSection",
    "build_nav",
    "collect",
    "get_nav",
    "merge",
    "sections",
    "validate",
]


def get_nav(request):
    """The nav for this request, as render-ready groups.

    Filtered by the request user's permissions, each link's ``href`` resolved and the
    active item marked (see ``render.build_nav``). A ``None`` request is treated as an
    anonymous user, so only entries with no ``permission`` appear.
    """
    return build_nav(request)
