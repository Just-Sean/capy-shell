"""Collect nav declared by installed apps and merge it into ordered sections.

capy-shell discovers each installed app's ``nav.py`` by convention and reads only its
``NAV`` data — never an app's models or views — so the shell stays generic and apps
stay unaware of it. The merge/sort logic is kept separate from app discovery so it can
be tested on plain data.
"""

from __future__ import annotations

import importlib

from django.apps import apps

from .schema import NavError, NavItem, NavSection, validate


def merge(sources: list[tuple[str, object]]) -> list[NavItem]:
    """Validate and merge (label, NAV-list) pairs into NavItems, keyed uniquely.

    ``sources`` is a list of (source label, raw NAV list) pairs. Raises NavError on an
    invalid entry or a key already used by another source.
    """
    items: dict[str, NavItem] = {}
    for label, raw in sources:
        if not isinstance(raw, (list, tuple)):
            raise NavError(f"{label}: NAV must be a list, got {type(raw).__name__}.")
        for entry in raw:
            item = validate(entry, source=label)
            if item.key in items:
                raise NavError(f"duplicate nav key {item.key!r} (declared more than once).")
            items[item.key] = item
    return list(items.values())


def sections(items: list[NavItem]) -> list[NavSection]:
    """Group items by section, ordered within and across sections.

    Items sort by (order, label); a section sorts by its lowest item order then title,
    so an untitled (top-level) group with the lowest order leads.
    """
    by_title: dict[str | None, list[NavItem]] = {}
    for item in items:
        by_title.setdefault(item.section, []).append(item)

    result = []
    for title, group in by_title.items():
        group.sort(key=lambda item: (item.order, item.label))
        result.append(NavSection(title=title, items=tuple(group)))
    result.sort(
        key=lambda section: (min(item.order for item in section.items), section.title or "")
    )
    return result


def _discover() -> list[tuple[str, object]]:
    found = []
    for config in apps.get_app_configs():
        module_name = f"{config.name}.nav"
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError as error:
            if error.name == module_name:
                continue  # This app simply has no nav.py.
            raise  # A real import error *inside* an existing nav.py — don't hide it.
        raw = getattr(module, "NAV", None)
        if raw is not None:
            found.append((config.label, raw))
    return found


def collect() -> list[NavSection]:
    """The merged nav from every installed app's nav.py, as ordered sections."""
    return sections(merge(_discover()))
