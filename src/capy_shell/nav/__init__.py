"""The capy-shell nav system.

Modules **declare** nav as plain data in their own ``nav.py`` (a ``NAV`` list of dicts
— see the README); they never import capy-shell. capy-shell **collects** and merges it.
``get_nav(request)`` is the stable interface the app-shell renders through — so a
different shell can read the same declarations.

This feature is the registry only. Permission filtering and active state (feature 7),
a REST endpoint (feature 7) and admin-editable DB overrides (feature 8) build on it;
``get_nav``'s signature stays the same as they do.
"""

from __future__ import annotations

from .collect import collect, merge, sections
from .schema import DEFAULT_ORDER, NavError, NavItem, NavSection, validate

__all__ = [
    "DEFAULT_ORDER",
    "NavError",
    "NavItem",
    "NavSection",
    "collect",
    "get_nav",
    "merge",
    "sections",
    "validate",
]


def get_nav(request):
    """The merged nav for this request, as ordered sections.

    MVP: the full collected nav. Feature 7 will filter it by the request user's
    permissions and mark the active item, and feature 8 will merge DB overrides; the
    signature stays the same, so callers (and a replacement shell) don't change.
    """
    return collect()
