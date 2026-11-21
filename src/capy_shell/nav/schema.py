"""The nav entry data contract: the fields a module declares, and their validation.

A module contributes nav by shipping a ``nav.py`` with a ``NAV`` list of plain dicts
(see the README). Those dicts are validated here into ``NavItem``s. The schema is the
stable contract between a module and whatever app-shell renders the nav, so a module
never imports the shell.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

DEFAULT_ORDER = 1000

# key/label are always required; url is required for a leaf but optional for a group
# (an item with `children`). Optional string fields must be non-blank when present.
REQUIRED = ("key", "label")
OPTIONAL_STR = ("icon", "section", "permission")
ALLOWED = {"key", "label", "url", "icon", "order", "section", "permission", "children"}
# Sub-items may not have their own `children` — nesting is one level deep.
ALLOWED_CHILD = ALLOWED - {"children"}

# Dangerous URL schemes a link must never use (they execute script when clicked).
# Browsers ignore ASCII whitespace and C0 control chars when parsing a scheme, so strip
# those before matching, or "java\tscript:" / "\x00javascript:" would slip through. A
# namespaced URL name like "app:view" is fine — it has no "javascript:"-style scheme.
_UNSAFE_SCHEME = re.compile(r"^(javascript|data|vbscript):", re.IGNORECASE)
_SCHEME_IGNORED = re.compile(r"[\x00-\x20]")


def _has_unsafe_scheme(url: str) -> bool:
    return bool(_UNSAFE_SCHEME.match(_SCHEME_IGNORED.sub("", url)))


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
    children: tuple[NavItem, ...] = ()


@dataclass(frozen=True)
class NavSection:
    """A group of nav items under an optional heading (``title`` None = top-level)."""

    title: str | None
    items: tuple[NavItem, ...]


@dataclass(frozen=True)
class NavLink:
    """A render-ready nav item: ``href`` resolved and ``active`` set for a request."""

    key: str
    label: str
    href: str
    icon: str | None
    active: bool
    children: tuple[NavLink, ...] = ()


@dataclass(frozen=True)
class NavGroup:
    """A render-ready section: its heading and its (permission-filtered) links."""

    title: str | None
    links: tuple[NavLink, ...]


def validate(entry: object, *, source: str = "", is_child: bool = False) -> NavItem:
    """Validate one declared nav dict into a NavItem, or raise NavError.

    A top-level item may have ``children`` (a list of the same shape, one level deep); a
    child may not. An item with children is a group whose ``url`` is optional.
    """
    where = f"{source} " if source else ""
    if not isinstance(entry, dict):
        raise NavError(f"{where}nav entry must be a dict, got {type(entry).__name__}.")

    unknown = set(entry) - (ALLOWED_CHILD if is_child else ALLOWED)
    if unknown:
        hint = (
            " (sub-items can't have their own children)" if is_child and "children" in entry else ""
        )
        raise NavError(
            f"{where}nav entry has unknown field(s): {', '.join(sorted(unknown))}.{hint}"
        )
    missing = set(REQUIRED) - set(entry)
    if missing:
        raise NavError(
            f"{where}nav entry is missing required field(s): {', '.join(sorted(missing))}."
        )

    for name in REQUIRED:
        value = entry[name]
        if not isinstance(value, str) or not value.strip():
            raise NavError(f"{where}nav entry {name!r} must be a non-blank string.")

    children = ()
    raw_children = entry.get("children")
    if raw_children is not None:
        if not isinstance(raw_children, (list, tuple)):
            raise NavError(f"{where}nav entry 'children' must be a list.")
        children = tuple(validate(child, source=source, is_child=True) for child in raw_children)

    # url is required for a leaf; a group (one with children) needs none of its own.
    if "url" in entry:
        url = entry["url"]
        if not isinstance(url, str) or not url.strip():
            raise NavError(f"{where}nav entry 'url' must be a non-blank string.")
        if _has_unsafe_scheme(url):
            raise NavError(f"{where}nav entry 'url' uses an unsafe scheme: {url!r}.")
    elif children:
        url = ""
    else:
        raise NavError(f"{where}nav entry is missing required field 'url'.")

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
        url=url,
        icon=entry.get("icon"),
        order=order,
        section=entry.get("section"),
        permission=entry.get("permission"),
        children=children,
    )
