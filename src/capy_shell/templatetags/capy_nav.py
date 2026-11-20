"""The ``{% shell_nav %}`` tag: render the collected nav for the current request.

Used by the shell's ``shell_nav`` block by default; a project can override that block.
"""

from __future__ import annotations

from django import template

from capy_shell.nav import get_nav

register = template.Library()


@register.inclusion_tag("capy_shell/nav.html", takes_context=True)
def shell_nav(context, orientation="vertical"):
    """Render the request's nav (permission-filtered, active-marked) as a daisyUI menu.

    ``orientation="horizontal"`` (the header top-nav on wide screens) lays the links out
    in a row and drops the section headings; the default vertical form keeps sections.
    """
    request = context.get("request")
    return {"groups": get_nav(request), "horizontal": orientation == "horizontal"}
