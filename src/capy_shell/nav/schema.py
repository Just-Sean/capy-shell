"""The nav entry data contract: the fields a module declares, and their validation.

A module contributes nav by shipping a ``nav.py`` with a ``NAV`` list of plain dicts
(see the README). Those dicts are validated here into ``NavItem``s. The schema is the
stable contract between a module and whatever app-shell renders the nav, so a module
never imports the shell.
"""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_ORDER = 1000

REQUIRED = ("key", "label", "url")
# Optional fields and the type each must be (when present and not None).
OPTIONAL_STR = ("icon", "section", "permission")
ALLOWED = set(REQUIRED) | set(OPTIONAL_STR) | {"order"}


class NavError(ValueError):
    """An invalid nav declaration."""


@dataclass(frozen=True)
class NavItem:
    """One resolved nav entry. See the README for what each field means."""

    key: str
    label: str
    url: str
    icon: str | None = None
    order: int = DEFAULT_ORDER
    section: str | None = None
    permission: str | None = None


@dataclass(frozen=True)
class NavSection:
    """A group of nav items under an optional heading (``title`` None = top-level)."""

    title: str | None
    items: tuple[NavItem, ...]


def validate(entry: object, *, source: str = "") -> NavItem:
    """Validate one declared nav dict into a NavItem, or raise NavError."""
    where = f"{source} " if source else ""
    if not isinstance(entry, dict):
        raise NavError(f"{where}nav entry must be a dict, got {type(entry).__name__}.")

    unknown = set(entry) - ALLOWED
    if unknown:
        raise NavError(f"{where}nav entry has unknown field(s): {', '.join(sorted(unknown))}.")
    missing = set(REQUIRED) - set(entry)
    if missing:
        raise NavError(
            f"{where}nav entry is missing required field(s): {', '.join(sorted(missing))}."
        )

    for name in REQUIRED:
        value = entry[name]
        if not isinstance(value, str) or not value.strip():
            raise NavError(f"{where}nav entry {name!r} must be a non-blank string.")
    for name in OPTIONAL_STR:
        value = entry.get(name)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise NavError(f"{where}nav entry {name!r} must be a non-blank string or None.")

    order = entry.get("order", DEFAULT_ORDER)
    # bool is an int subclass; exclude it so order=True isn't quietly accepted.
    if not isinstance(order, int) or isinstance(order, bool):
        raise NavError(f"{where}nav entry 'order' must be an int.")

    return NavItem(
        key=entry["key"],
        label=entry["label"],
        url=entry["url"],
        icon=entry.get("icon"),
        order=order,
        section=entry.get("section"),
        permission=entry.get("permission"),
    )
