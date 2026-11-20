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


def build_nav(request) -> list[NavGroup]:
    """The permission-filtered, href-resolved, active-marked nav for this request."""
    user = getattr(request, "user", None)
    path = getattr(request, "path", "")
    groups = []
    for section in collect():
        links = []
        for item in section.items:
            if item.permission and not (user is not None and user.has_perm(item.permission)):
                continue
            href = _resolve_href(item.url)
            links.append(
                NavLink(
                    key=item.key,
                    label=item.label,
                    href=href,
                    icon=item.icon,
                    active=_is_active(path, href),
                )
            )
        if links:
            groups.append(NavGroup(title=section.title, links=tuple(links)))
    return groups
