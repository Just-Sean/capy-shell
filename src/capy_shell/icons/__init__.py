"""Inline Lucide SVG icons.

The ``*.svg`` files in this directory are vendored from Lucide (see ``LICENSE`` and
``scripts/fetch_icons.py``). This module resolves an icon name to its SVG text and
caches it; the ``{% icon %}`` template tag (``templatetags/capy_icons.py``) renders
it. Projects add their own icons through the ``CAPY_SHELL_ICON_DIRS`` setting.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from capy_shell import conf

# Lucide names are lowercase kebab-case. The pattern also blocks path traversal
# (no "/", "." or "..") since the name becomes part of a file path below.
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

# The icons that ship with capy-shell live next to this file.
PACKAGE_ICONS = Path(__file__).resolve().parent


class IconError(ValueError):
    """An icon name that is invalid, or an icon that can't be found."""


def _search_dirs() -> tuple[str, ...]:
    # Project directories first, so a project can override a built-in; then ours.
    project_dirs = tuple(str(directory) for directory in conf.get("CAPY_SHELL_ICON_DIRS"))
    return (*project_dirs, str(PACKAGE_ICONS))


@lru_cache(maxsize=512)
def _load(name: str, dirs: tuple[str, ...]) -> str:
    for directory in dirs:
        path = Path(directory) / f"{name}.svg"
        if path.is_file():
            return path.read_text(encoding="utf-8").strip()
    raise IconError(
        f"No icon named {name!r}. Ship it in an icons directory "
        f"(see CAPY_SHELL_ICON_DIRS) or choose another name."
    )


def get_svg(name: str) -> str:
    """The SVG markup for an icon name, searched across the configured directories.

    Raises IconError for an invalid name or an icon that isn't found. The cache is
    keyed on the configured directories, so a project (or a test) that changes
    CAPY_SHELL_ICON_DIRS is not served a stale result.
    """
    if not NAME_RE.fullmatch(name):
        raise IconError(
            f"Invalid icon name {name!r}: use lowercase letters, digits and hyphens."
        )
    return _load(name, _search_dirs())
