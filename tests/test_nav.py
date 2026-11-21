"""The nav registration contract: schema validation, merge/sections, and collection."""

import pytest

from capy_shell import nav
from capy_shell.nav import (
    NavError,
    NavGroup,
    NavItem,
    NavLink,
    checks,
    collect,
    get_nav,
    merge,
    sections,
    validate,
)
from capy_shell.nav.collect import _import_nav
from capy_shell.nav.render import _build_link, _is_active, _resolve_href, build_nav


class _FakeUser:
    def __init__(self, *perms):
        self._perms = set(perms)

    def has_perm(self, perm):
        return perm in self._perms


class _FakeRequest:
    def __init__(self, path="/", *perms):
        self.path = path
        self.user = _FakeUser(*perms)


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
        {"key": "   ", "label": "L", "url": "u"},  # whitespace only
        {"key": 1, "label": "L", "url": "u"},  # not a string
    ],
)
def test_validate_rejects_blank_or_non_string_required(bad):
    with pytest.raises(NavError, match="non-blank string"):
        validate(bad)


@pytest.mark.parametrize("section", ["", "   "])
def test_validate_rejects_blank_optional(section):
    with pytest.raises(NavError, match="non-blank string or None"):
        validate({"key": "k", "label": "L", "url": "u", "section": section})


@pytest.mark.parametrize("order", ["5", 1.5, True])
def test_validate_rejects_non_int_order(order):
    with pytest.raises(NavError, match="'order' must be an int"):
        validate({"key": "k", "label": "L", "url": "u", "order": order})


def test_validate_rejects_a_non_dict():
    with pytest.raises(NavError, match="must be a dict"):
        validate(["not", "a", "dict"])


@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(1)",
        " DATA:text/html",
        "vbscript:x",
        "JavaScript:alert(1)",  # mixed case
        "java\tscript:alert(1)",  # TAB inside the scheme (browsers strip it)
        "java\nscript:alert(1)",  # newline inside the scheme
        "\x00javascript:alert(1)",  # leading NUL (browsers strip it)
    ],
)
def test_validate_rejects_unsafe_url_schemes(url):
    with pytest.raises(NavError, match="unsafe scheme"):
        validate({"key": "k", "label": "L", "url": url})


# --- merge + sections ---------------------------------------------------------


def test_merge_combines_sources():
    items = merge(
        [
            ("a", [{"key": "a1", "label": "A1", "url": "u"}]),
            ("b", [{"key": "b1", "label": "B1", "url": "u"}]),
        ]
    )
    assert {item.key for item in items} == {"a1", "b1"}


def test_merge_rejects_duplicate_keys_across_sources():
    with pytest.raises(NavError, match="duplicate nav key 'dup'"):
        merge(
            [
                ("a", [{"key": "dup", "label": "A", "url": "u"}]),
                ("b", [{"key": "dup", "label": "B", "url": "u"}]),
            ]
        )


def test_merge_rejects_duplicate_keys_within_one_source():
    with pytest.raises(NavError, match="duplicate nav key 'dup'"):
        merge(
            [
                (
                    "a",
                    [
                        {"key": "dup", "label": "A", "url": "u"},
                        {"key": "dup", "label": "B", "url": "u"},
                    ],
                )
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


# --- rendering: permissions, href, active ------------------------------------


def test_get_nav_returns_render_ready_groups():
    groups = get_nav(_FakeRequest())
    assert groups and all(isinstance(group, NavGroup) for group in groups)
    assert all(isinstance(link, NavLink) for group in groups for link in group.links)


def test_permission_filtering_hides_entries_without_the_perm():
    keys = {link.key for group in get_nav(_FakeRequest()) for link in group.links}
    assert "b:settings" not in keys  # requires "b.view_settings"
    assert "a:home" in keys  # no permission -> always shown


def test_permission_filtering_shows_entries_with_the_perm():
    request = _FakeRequest("/", "b.view_settings")
    keys = {link.key for group in get_nav(request) for link in group.links}
    assert "b:settings" in keys


def test_none_request_is_treated_as_anonymous():
    keys = {link.key for group in get_nav(None) for link in group.links}
    assert "b:settings" not in keys


def test_active_item_is_marked_by_path():
    # b:top's url "top" isn't a reversible name, so its href is the literal "top".
    groups = build_nav(_FakeRequest("top"))
    active = {link.key for group in groups for link in group.links if link.active}
    assert active == {"b:top"}


def test_resolve_href_reverses_a_url_name():
    assert _resolve_href("admin:index") == "/admin/"


def test_resolve_href_passes_through_a_literal_path():
    assert _resolve_href("/somewhere/") == "/somewhere/"


# --- nested items (one level) ------------------------------------------------


def test_validate_accepts_a_group_with_children():
    item = validate(
        {"key": "g", "label": "G", "children": [{"key": "c", "label": "C", "url": "/x/"}]}
    )
    assert item.url == ""  # a group needs no url of its own
    assert len(item.children) == 1 and item.children[0].key == "c"


def test_validate_leaf_still_requires_url():
    with pytest.raises(NavError, match="missing required field 'url'"):
        validate({"key": "k", "label": "L"})


def test_validate_rejects_two_levels_of_nesting():
    with pytest.raises(NavError, match="sub-items can't have their own children"):
        validate(
            {
                "key": "g",
                "label": "G",
                "children": [
                    {
                        "key": "c",
                        "label": "C",
                        "url": "/x/",
                        "children": [{"key": "gc", "label": "GC", "url": "/y/"}],
                    }
                ],
            }
        )


def test_validate_rejects_non_list_children():
    with pytest.raises(NavError, match="'children' must be a list"):
        validate({"key": "g", "label": "G", "children": "nope"})


def test_build_link_filters_children_and_marks_the_trail_active():
    item = NavItem(
        key="g",
        label="G",
        url="",
        children=(
            NavItem(key="c1", label="C1", url="/a/"),
            NavItem(key="c2", label="C2", url="/b/", permission="x.perm"),
        ),
    )
    link = _build_link(item, _FakeUser(), "/a/")  # no permissions, on /a/
    assert link is not None
    assert [c.key for c in link.children] == ["c1"]  # c2 needs x.perm -> hidden
    assert link.href == "" and link.active  # group, active because child c1 is


def test_build_link_drops_a_group_with_no_visible_children():
    item = NavItem(
        key="g",
        label="G",
        url="",
        children=(NavItem(key="c", label="C", url="/x/", permission="need"),),
    )
    assert _build_link(item, _FakeUser(), "/") is None


@pytest.mark.parametrize(
    "path,href,active",
    [
        ("/", "/", True),
        ("/x/", "/", False),
        ("/x/", "/x/", True),
        ("/x/y/", "/x/", True),  # a child path marks the section parent active
        ("/other/", "/x/", False),
    ],
)
def test_is_active(path, href, active):
    assert _is_active(path, href) is active


# --- _import_nav: skip vs re-raise -------------------------------------------


def test_import_nav_finds_an_apps_nav_module():
    module = _import_nav("tests.navapp_a")
    assert module is not None and hasattr(module, "NAV")


def test_import_nav_returns_none_when_no_nav_module():
    # An installed app without a nav.py is skipped, not an error.
    assert _import_nav("django.contrib.auth") is None


def test_import_nav_reraises_a_broken_nav_module():
    # tests/navprobe_broken/nav.py imports a missing module; that real error must
    # propagate, not be mistaken for "this app has no nav.py".
    with pytest.raises(ModuleNotFoundError, match="capy_shell_this_module_does_not_exist"):
        _import_nav("tests.navprobe_broken")


# --- the startup system check ------------------------------------------------


def test_check_nav_passes_for_valid_nav():
    assert checks.check_nav(None) == []


def test_check_nav_reports_invalid_nav(monkeypatch):
    def boom():
        raise NavError("duplicate nav key 'x'")

    monkeypatch.setattr(checks, "collect", boom)
    errors = checks.check_nav(None)
    assert len(errors) == 1 and errors[0].id == checks.NAV_ERROR_ID
