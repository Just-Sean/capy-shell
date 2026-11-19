"""The ``{% icon %}`` template tag: inline a vendored SVG icon.

See ``capy_shell.icons`` for how an icon name resolves to its SVG, and the README for
the tag's arguments and how a project adds its own icons.
"""

from __future__ import annotations

import re

from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from capy_shell.icons import IconError, get_svg

register = template.Library()

# The opening tag of a (normalized, vendored) icon SVG.
_SVG_OPEN = re.compile(r"<svg\b", re.IGNORECASE)


@register.simple_tag
def icon(name, size=24, label="", **attrs):
    """Render the named icon as an inline ``<svg>``.

    ``size`` sets the width and height; ``class`` adds CSS classes. The icon is
    decorative by default (``aria-hidden``); pass ``label="…"`` to make it a
    meaningful image (``role="img"`` with an accessible name).
    """
    css = attrs.pop("class", "")
    if attrs:
        raise template.TemplateSyntaxError(
            f"icon tag got unexpected argument(s): {', '.join(sorted(attrs))}. "
            f"It takes name, size, label and class."
        )

    svg = get_svg(name)
    match = _SVG_OPEN.search(svg)
    if match is None:  # pragma: no cover - the vendored icons are all well-formed
        raise IconError(f"Icon {name!r} is not valid SVG (no <svg> element).")

    # Escape every injected value: size/class/label may be template variables.
    injected = format_html(' width="{}" height="{}"', size, size)
    if css:
        injected += format_html(' class="{}"', css)
    if label:
        injected += format_html(' role="img" aria-label="{}"', label)
    else:
        injected += mark_safe(' aria-hidden="true" focusable="false"')

    # The SVG text is trusted (a vendored file); `injected` is escaped. Splice the
    # attributes in after "<svg" and mark the whole thing safe.
    cut = match.end()
    return mark_safe(svg[:cut] + injected + svg[cut:])  # noqa: S308 (trusted vendored SVG; injected attrs escaped)
