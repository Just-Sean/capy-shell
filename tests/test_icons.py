"""The {% icon %} tag and the icon loader (feature 5)."""

from pathlib import Path

import pytest
from django.template import Context, Template, TemplateSyntaxError

import capy_shell
from capy_shell.icons import IconError, get_svg

ICONS_DIR = Path(capy_shell.__file__).parent / "icons"
# Normalized so the tag owns size and classes; themeable via currentColor.
A_MINIMAL_SVG = '<svg viewBox="0 0 24 24" stroke="currentColor"><path d="M4 4h16"/></svg>\n'


def render(body, **context):
    return Template("{% load capy_icons %}" + body).render(Context(context))


# --- the loader ---------------------------------------------------------------


def test_curated_icons_ship_and_are_normalized():
    # The starter set is vendored, and each root <svg> has no width/height/class
    # (the tag adds those) but keeps a viewBox and currentColor so it themes.
    for name in ["menu", "x", "chevron-down", "house", "user"]:
        svg = (ICONS_DIR / f"{name}.svg").read_text()
        opening = svg[: svg.index(">") + 1]
        assert "<svg" in opening
        # No root width/height/class (the tag adds them). Leading space so this
        # doesn't match the legitimate `stroke-width` attribute Lucide keeps.
        assert " width=" not in opening and " height=" not in opening
        assert " class=" not in opening
        assert "viewBox" in opening
        assert "currentColor" in svg


def test_lucide_license_ships_with_the_icons():
    assert (ICONS_DIR / "LICENSE").is_file()


def test_unknown_icon_errors_clearly():
    with pytest.raises(IconError, match="No icon named 'definitely-not-an-icon'"):
        get_svg("definitely-not-an-icon")


@pytest.mark.parametrize("bad", ["../secrets", "a/b", "Menu", "a_b", "", "a.b"])
def test_invalid_names_are_rejected(bad):
    with pytest.raises(IconError, match="Invalid icon name"):
        get_svg(bad)


@pytest.mark.parametrize("bad", [None, 123, 4.5])
def test_non_string_names_raise_iconerror_not_typeerror(bad):
    # A dynamic name that resolves to None/a number must still fail cleanly.
    with pytest.raises(IconError, match="Invalid icon name"):
        get_svg(bad)


def test_a_project_can_add_and_override_icons(settings, tmp_path):
    (tmp_path / "menu.svg").write_text(A_MINIMAL_SVG)  # same name as a built-in
    (tmp_path / "custom.svg").write_text(A_MINIMAL_SVG)
    settings.CAPY_SHELL_ICON_DIRS = [str(tmp_path)]
    # The project's dir is searched first, so it overrides the built-in "menu"...
    assert get_svg("menu") == A_MINIMAL_SVG.strip()
    # ...and adds brand-new icons...
    assert "M4 4h16" in get_svg("custom")
    # ...while a built-in the project didn't override still falls through to ours.
    assert "<svg" in get_svg("user")


# --- the tag ------------------------------------------------------------------


def test_icon_tag_inlines_the_svg():
    out = render('{% icon "menu" %}')
    assert "<svg" in out and "viewBox" in out
    assert 'width="24" height="24"' in out  # the default size


def test_size_and_class_are_applied():
    out = render('{% icon "menu" size=32 class="h-5 w-5" %}')
    assert 'width="32" height="32"' in out
    assert 'class="h-5 w-5"' in out


def test_decorative_by_default():
    out = render('{% icon "menu" %}')
    assert 'aria-hidden="true"' in out
    assert 'focusable="false"' in out
    assert "role=" not in out


def test_label_makes_it_a_meaningful_image():
    out = render('{% icon "house" label="Home" %}')
    assert 'role="img"' in out
    assert 'aria-label="Home"' in out
    assert "aria-hidden" not in out


def test_label_is_escaped():
    out = render('{% icon "house" label=label %}', label='A "quote" & <tag>')
    assert "&quot;quote&quot;" in out
    assert "&lt;tag&gt;" in out
    assert "<tag>" not in out


def test_unexpected_argument_errors():
    with pytest.raises(TemplateSyntaxError, match="unexpected argument"):
        render('{% icon "menu" title="nope" %}')


def test_a_malformed_project_icon_errors(settings, tmp_path):
    # A project-supplied file that isn't an <svg> fails cleanly, not silently.
    (tmp_path / "broken.svg").write_text("not an svg")
    settings.CAPY_SHELL_ICON_DIRS = [str(tmp_path)]
    with pytest.raises(IconError, match="not valid SVG"):
        render('{% icon "broken" %}')


@pytest.mark.parametrize("bad", [0, -5, "abc", None])
def test_non_positive_or_non_numeric_size_errors(bad):
    # size=0 would render an invisible icon, a negative size invalid SVG — reject both.
    with pytest.raises(TemplateSyntaxError, match="size must be a positive number"):
        render("{% icon 'menu' size=s %}", s=bad)
