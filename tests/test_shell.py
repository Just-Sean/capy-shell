"""The shell's settings (conf), context processor (feature 1) and content CSS (feature 2)."""

from pathlib import Path

import capy_shell
from capy_shell import conf
from capy_shell.context_processors import shell


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


def test_content_stylesheet_ships_and_is_scoped():
    css = (Path(capy_shell.__file__).parent / "static/capy_shell/shell.css").read_text()
    # Scoped to the content area, so it never touches the header, nav or daisyUI classes.
    assert "#capy-shell-main a:not([class])" in css
    # An underline, not colour alone (WCAG 1.4.1, use of colour).
    assert "underline" in css
    # The theme's colour, with a safe fallback when no theme is active.
    assert "var(--color-primary" in css
