"""Turn the collected nav into render-ready groups for one request.

``build_nav(request)`` filters entries by the request user's permissions, resolves each
``url`` to an ``href`` (a URL name via ``reverse``, else the literal path), and marks the
item matching the current path as active.
"""

from __future__ import annotations

from django.urls import NoReverseMatch, reverse

from .collect import collect
from .schema import NavGroup, NavLink


def _resolve_href(url: str) -> str:
    # A URL name resolves via reverse; anything else is already a path or absolute URL
    # (its scheme was checked as safe when the entry was validated).
    try:
        return reverse(url)
    except NoReverseMatch:
        return url


def _is_active(path: str, href: str) -> bool:
    if not path or not href:
        return False
    if href == "/":
        return path == "/"
    return path == href or path.startswith(href.rstrip("/") + "/")


def _build_link(item, user, path) -> NavLink | None:
    """A render-ready link for one item, or None if the user can't see it.

    Recurses one level into children; a group with no own url and no visible children is
    dropped, and a parent is "active" if it or any visible child is active (active trail).
    """
    if item.permission and not (user is not None and user.has_perm(item.permission)):
        return None
    children = tuple(
        link for child in item.children if (link := _build_link(child, user, path)) is not None
    )
    if item.children and not children and not item.url:
        return None  # an empty group leads nowhere.
    href = _resolve_href(item.url) if item.url else ""
    active = (_is_active(path, href) if href else False) or any(c.active for c in children)
    return NavLink(
        key=item.key, label=item.label, href=href, icon=item.icon, active=active, children=children
    )


def build_nav(request) -> list[NavGroup]:
    """The permission-filtered, href-resolved, active-marked nav for this request."""
    user = getattr(request, "user", None)
    path = getattr(request, "path", "")
    groups = []
    for section in collect():
        links = tuple(
            link for item in section.items if (link := _build_link(item, user, path)) is not None
        )
        if links:
            groups.append(NavGroup(title=section.title, links=links))
    return groups
