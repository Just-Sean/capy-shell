"""The nav registration contract: schema validation, merge/sections, and collection."""

import pytest
from django.test import RequestFactory

from capy_shell import nav
from capy_shell.nav import (
    NavError,
    NavItem,
    NavSection,
    collect,
    get_nav,
    merge,
    sections,
    validate,
)

# --- schema -------------------------------------------------------------------


def test_validate_accepts_a_full_entry():
    item = validate(
        {
            "key": "k",
            "label": "L",
            "url": "u",
            "icon": "house",
            "order": 5,
            "section": "S",
            "permission": "app.view",
        }
    )
    assert isinstance(item, NavItem)
    assert item.key == "k" and item.icon == "house" and item.order == 5


def test_validate_defaults_optional_fields():
    item = validate({"key": "k", "label": "L", "url": "u"})
    assert item.icon is None and item.section is None and item.permission is None
    assert item.order == nav.DEFAULT_ORDER


@pytest.mark.parametrize(
    "entry",
    [
        {"label": "L", "url": "u"},  # missing key
        {"key": "k", "url": "u"},  # missing label
        {"key": "k", "label": "L"},  # missing url
    ],
)
def test_validate_requires_key_label_url(entry):
    with pytest.raises(NavError, match="missing required field"):
        validate(entry)


def test_validate_rejects_unknown_field():
    with pytest.raises(NavError, match="unknown field"):
        validate({"key": "k", "label": "L", "url": "u", "href": "x"})


@pytest.mark.parametrize(
    "bad",
    [
        {"key": "", "label": "L", "url": "u"},  # empty string
        {"key": 1, "label": "L", "url": "u"},  # not a string
    ],
)
def test_validate_rejects_bad_required_types(bad):
    with pytest.raises(NavError, match="non-empty string"):
        validate(bad)


@pytest.mark.parametrize("order", ["5", 1.5, True])
def test_validate_rejects_non_int_order(order):
    with pytest.raises(NavError, match="'order' must be an int"):
        validate({"key": "k", "label": "L", "url": "u", "order": order})


def test_validate_rejects_a_non_dict():
    with pytest.raises(NavError, match="must be a dict"):
        validate(["not", "a", "dict"])


# --- merge + sections ---------------------------------------------------------


def test_merge_combines_sources():
    items = merge(
        [
            ("a", [{"key": "a1", "label": "A1", "url": "u"}]),
            ("b", [{"key": "b1", "label": "B1", "url": "u"}]),
        ]
    )
    assert {item.key for item in items} == {"a1", "b1"}


def test_merge_rejects_duplicate_keys():
    with pytest.raises(NavError, match="duplicate nav key 'dup'"):
        merge(
            [
                ("a", [{"key": "dup", "label": "A", "url": "u"}]),
                ("b", [{"key": "dup", "label": "B", "url": "u"}]),
            ]
        )


def test_merge_rejects_non_list_nav():
    with pytest.raises(NavError, match="NAV must be a list"):
        merge([("a", {"key": "x"})])


def test_sections_group_and_order():
    items = [
        NavItem(key="x", label="X", url="u", order=30, section="Main"),
        NavItem(key="y", label="Y", url="u", order=10, section="Main"),
        NavItem(key="z", label="Z", url="u", order=5, section=None),
    ]
    result = sections(items)
    # The top-level (None) group leads (lowest order), then Main sorted within.
    assert [s.title for s in result] == [None, "Main"]
    assert [item.key for item in result[1].items] == ["y", "x"]


# --- collection over installed apps ------------------------------------------


def test_collect_merges_installed_apps_nav():
    keys = {item.key for section in collect() for item in section.items}
    # tests/navapp_a and navapp_b declare these; capy_shell and the django.contrib
    # apps have no nav.py and are skipped.
    assert {"a:home", "a:about", "b:settings", "b:top"} <= keys


def test_collect_orders_sections():
    titles = [section.title for section in collect()]
    assert None in titles and "Main" in titles
    # b:top (order 5, no section) leads the Main section (lowest order 10).
    assert titles.index(None) < titles.index("Main")


def test_collect_carries_optional_fields():
    items = {item.key: item for section in collect() for item in section.items}
    assert items["b:settings"].icon == "settings"
    assert items["b:settings"].permission == "b.view_settings"


def test_get_nav_returns_sections():
    result = get_nav(RequestFactory().get("/"))
    assert result and all(isinstance(section, NavSection) for section in result)
