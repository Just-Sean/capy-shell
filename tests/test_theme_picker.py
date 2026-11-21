"""The theme picker: capy-shell asks capy-theme for the catalog, shows light and dark
themes, remembers a pick per scheme, and loads the chosen light and dark themes.

The catalog and assets come from the stand-in capy-theme tags (tests/capy_theme_stub.py):
light themes dawn (default) and paper; dark themes midnight (default) and ink.
"""

from django.template.loader import render_to_string
from django.test import Client, RequestFactory

from capy_shell.templatetags.capy_shell_theme import scheme_themes, theme_slots


def _render(template, **cookies):
    request = RequestFactory().get("/here/")
    request.COOKIES.update(cookies)
    return render_to_string(template, request=request)


# The picker


def test_picker_lists_light_and_dark_themes_in_groups():
    html = _render("capy_shell/base.html")
    assert "Light" in html and "Dark" in html
    for name in ("Dawn", "Paper", "Midnight", "Ink"):
        assert name in html
    assert "/shell/set-theme/light/paper/" in html
    assert "/shell/set-theme/dark/midnight/" in html


def test_picker_links_come_back_to_the_current_page():
    html = _render("capy_shell/base.html")
    assert "next=/here/" in html


def test_picker_marks_the_default_slots_when_nothing_is_picked():
    html = _render("capy_shell/_theme_picker.html")
    # Dawn (default light) and Midnight (default dark) are current.
    assert html.count('aria-current="true"') == 2
    dawn = html.split("/shell/set-theme/light/dawn/")[1].split("</a>")[0]
    assert 'aria-current="true"' in dawn


def test_picker_marks_the_picked_theme_over_the_default():
    html = _render("capy_shell/_theme_picker.html", capy_shell_light_theme="paper")
    paper = html.split("/shell/set-theme/light/paper/")[1].split("</a>")[0]
    assert 'aria-current="true"' in paper
    dawn = html.split("/shell/set-theme/light/dawn/")[1].split("</a>")[0]
    assert 'aria-current="true"' not in dawn


# Slot resolution (theme_slots / scheme_themes)


def render_catalog():
    from tests.capy_theme_stub import theme_catalog

    return theme_catalog()


def test_scheme_themes_filters_by_scheme():
    catalog = render_catalog()
    assert [t["slug"] for t in scheme_themes(catalog, "light")] == ["dawn", "paper"]
    assert [t["slug"] for t in scheme_themes(catalog, "dark")] == ["midnight", "ink"]


def test_theme_slots_uses_the_pick_then_the_default():
    catalog = render_catalog()
    # No picks: the defaults.
    slots = theme_slots(catalog)
    assert slots["light"]["slug"] == "dawn"
    assert slots["dark"]["slug"] == "midnight"
    # A custom pick wins for its scheme; the other stays on its default.
    slots = theme_slots(catalog, light_pick="paper", dark_pick="")
    assert slots["light"]["slug"] == "paper"
    assert slots["dark"]["slug"] == "midnight"


def test_theme_slots_ignores_a_pick_that_isnt_in_the_catalog():
    catalog = render_catalog()
    slots = theme_slots(catalog, light_pick="gone", dark_pick="also-gone")
    assert slots["light"]["slug"] == "dawn"  # falls back to the default
    assert slots["dark"]["slug"] == "midnight"


def test_theme_slots_is_empty_without_a_catalog():
    assert theme_slots([]) == {"light": None, "dark": None}


# Loading the chosen themes (the host-head stylesheet partial)


def test_stylesheet_partial_links_both_slots():
    html = _render("capy_shell/_theme_stylesheet.html")
    assert '<link rel="stylesheet" href="/theme/dawn.css">' in html
    assert '<link rel="stylesheet" href="/theme/midnight.css">' in html


def test_stylesheet_partial_follows_the_picks():
    html = _render(
        "capy_shell/_theme_stylesheet.html",
        capy_shell_light_theme="paper",
        capy_shell_dark_theme="ink",
    )
    assert '<link rel="stylesheet" href="/theme/paper.css">' in html
    assert '<link rel="stylesheet" href="/theme/ink.css">' in html
    assert "/theme/dawn.css" not in html


# The brand (the light-slot theme's logo, or its name when there's no logo)


def test_brand_shows_the_light_slot_theme():
    html = _render("capy_shell/_brand.html")
    assert "Dawn" in html  # the stub has no logo image, so the site name shows


def test_brand_follows_the_light_pick():
    html = _render("capy_shell/_brand.html", capy_shell_light_theme="paper")
    assert "Paper" in html


# The set-theme view


def test_set_theme_sets_the_scheme_cookie_and_comes_back():
    response = Client().get("/shell/set-theme/light/paper/?next=/here/")
    assert response.status_code == 302
    assert response.headers["Location"] == "/here/"
    assert response.cookies["capy_shell_light_theme"].value == "paper"


def test_set_theme_sets_the_dark_cookie_for_a_dark_pick():
    response = Client().get("/shell/set-theme/dark/ink/?next=/here/")
    assert response.cookies["capy_shell_dark_theme"].value == "ink"


def test_set_theme_only_returns_to_a_url_on_this_site():
    response = Client().get("/shell/set-theme/light/paper/?next=https://evil.example/x")
    assert response.status_code == 302
    assert response.headers["Location"] == "/"


def test_set_theme_rejects_an_unknown_scheme():
    assert Client().get("/shell/set-theme/bogus/paper/").status_code == 404
