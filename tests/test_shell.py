"""The shell's settings (conf), context processor, regions, content CSS and nav drawer."""

from pathlib import Path

from django.template.loader import render_to_string
from django.test import RequestFactory

import capy_shell
from capy_shell import conf
from capy_shell.context_processors import shell

BASE_TEMPLATE = Path(capy_shell.__file__).parent / "templates/capy_shell/base.html"


def _render_shell():
    # Render the shell base through the stand-in project (tests/settings.py wires the
    # context processor, a parent base.html and the no-op capy_theme tags).
    return render_to_string("capy_shell/base.html", request=RequestFactory().get("/"))


def test_conf_returns_the_defaults():
    assert conf.get("CAPY_SHELL_CONTENT_MAX_WIDTH") == "max-w-7xl"
    assert conf.get("CAPY_SHELL_CONTENT_PADDING") == "px-4 py-6"
    assert conf.get("CAPY_SHELL_HOME_URL") == "/"


def test_conf_reads_the_project_setting(settings):
    settings.CAPY_SHELL_CONTENT_MAX_WIDTH = "max-w-3xl"
    assert conf.get("CAPY_SHELL_CONTENT_MAX_WIDTH") == "max-w-3xl"


def test_context_processor_exposes_the_config(settings):
    settings.CAPY_SHELL_CONTENT_PADDING = "p-2"
    ctx = shell(request=None)["shell"]
    assert ctx["content_padding"] == "p-2"
    assert ctx["content_max_width"] == "max-w-7xl"
    assert ctx["home_url"] == "/"


def test_conf_defaults_for_the_regions():
    assert conf.get("CAPY_SHELL_HEADER_STICKY") is True
    assert conf.get("CAPY_SHELL_SIDEBAR") is True
    assert conf.get("CAPY_SHELL_SIDEBAR_WIDTH") == "w-64"
    assert conf.get("CAPY_SHELL_SIDEBAR_STICKY") is True
    assert conf.get("CAPY_SHELL_ASIDE") is False
    assert conf.get("CAPY_SHELL_ASIDE_WIDTH") == "w-64"
    assert conf.get("CAPY_SHELL_ASIDE_STICKY") is True
    assert conf.get("CAPY_SHELL_FOOTER") is False


def test_context_processor_exposes_the_region_config(settings):
    settings.CAPY_SHELL_SIDEBAR = False
    settings.CAPY_SHELL_ASIDE = True
    ctx = shell(request=None)["shell"]
    assert ctx["sidebar"] is False  # the project's override
    assert ctx["aside"] is True  # the project's override
    assert ctx["header_sticky"] is True  # still the default
    assert ctx["footer"] is False  # still the default
    assert ctx["sidebar_width"] == "w-64"


def test_regions_render_only_when_their_setting_is_on(settings):
    # Defaults: sidebar + sticky header, no aside, no footer.
    html = _render_shell()
    assert "border-r" in html  # the sidebar wrapper
    assert "sticky top-0" in html  # the header is sticky
    assert "<aside" not in html  # aside off
    assert "<footer" not in html  # footer off

    settings.CAPY_SHELL_SIDEBAR = False
    settings.CAPY_SHELL_ASIDE = True
    settings.CAPY_SHELL_FOOTER = True
    settings.CAPY_SHELL_HEADER_STICKY = False
    html = _render_shell()
    assert "border-r" not in html  # sidebar gone
    assert "<aside" in html  # aside on
    assert "<footer" in html  # footer on
    assert "sticky top-0" not in html  # header no longer sticky


def test_sidebar_is_a_drawer_with_a_burger():
    html = _render_shell()
    # A hidden checkbox holds the open/closed state (toggled with no JavaScript).
    assert 'id="capy-shell-drawer-toggle"' in html
    # The burger names and controls the drawer for assistive tech.
    assert 'id="capy-shell-drawer-button"' in html
    assert 'aria-controls="capy-shell-nav"' in html
    assert 'aria-expanded="false"' in html
    # The drawer wrapper is a labeled <nav> landmark with the controlled id.
    assert '<nav id="capy-shell-nav" aria-label=' in html
    # The backdrop that closes the drawer.
    assert 'id="capy-shell-overlay"' in html


def test_drawer_script_is_loaded_deferred():
    html = _render_shell()
    assert "capy_shell/drawer.js" in html
    assert "defer" in html


def test_no_drawer_when_the_sidebar_is_off(settings):
    settings.CAPY_SHELL_SIDEBAR = False
    html = _render_shell()
    assert 'id="capy-shell-drawer-toggle"' not in html
    assert 'id="capy-shell-drawer-button"' not in html
    assert 'id="capy-shell-nav"' not in html
    assert 'id="capy-shell-overlay"' not in html


def test_drawer_styles_and_script_ship():
    base = Path(capy_shell.__file__).parent
    css = (base / "static/capy_shell/shell.css").read_text()
    # Off-canvas below md, slid in by the checkbox via :has(), reduced-motion aware.
    assert "#capy-shell-nav" in css
    assert ":has(#capy-shell-drawer-toggle:checked)" in css
    assert "prefers-reduced-motion" in css
    js = (base / "static/capy_shell/drawer.js").read_text()
    # The script enhances the same checkbox and keeps the burger's state in sync.
    assert "capy-shell-drawer-toggle" in js
    assert "aria-expanded" in js
    # The focus-trap counts <summary> as a tab stop (a nav can be built from
    # <details><summary>), so it must be in the focusable selector.
    assert "summary" in js


def test_safelist_comment_covers_the_settings_driven_classes():
    # Classes that reach the template from settings can't be seen by Tailwind's
    # scanner, so the shipped defaults must appear literally in base.html (its
    # tailwind-safelist comment) or Tailwind won't build them. Guards against drift.
    base = BASE_TEMPLATE.read_text()
    class_settings = [
        "CAPY_SHELL_SIDEBAR_WIDTH",
        "CAPY_SHELL_ASIDE_WIDTH",
        "CAPY_SHELL_CONTENT_MAX_WIDTH",
        "CAPY_SHELL_CONTENT_PADDING",
    ]
    for name in class_settings:
        for token in conf.DEFAULTS[name].split():
            assert token in base, f"{token!r} (default of {name}) is missing from base.html"


def test_content_stylesheet_ships_and_is_scoped():
    css = (Path(capy_shell.__file__).parent / "static/capy_shell/shell.css").read_text()
    # Scoped to the content area, so it never touches the header, nav or daisyUI classes.
    assert "#capy-shell-main a:not([class])" in css
    # An underline, not colour alone (WCAG 1.4.1, use of colour).
    assert "underline" in css
    # The theme's colour, with a safe fallback when no theme is active.
    assert "var(--color-primary" in css
