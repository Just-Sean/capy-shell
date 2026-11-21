"""The shell's views: remembering the visitor's theme choice."""

from django.http import HttpResponseRedirect
from django.utils.http import url_has_allowed_host_and_scheme

from .context_processors import THEME_COOKIE

COOKIE_MAX_AGE = 60 * 60 * 24 * 365  # a year, so the choice survives closing the browser


def set_theme(request, slug):
    """Remember the visitor's chosen theme (its slug) in a cookie, then go back.

    A plain link, so the picker works without JavaScript. The slug isn't validated here:
    capy-theme's ``{% theme_assets %}`` ignores an unknown / unpublished / not-offered one
    and the templates fall back to the default theme when the page renders.
    """
    response = HttpResponseRedirect(_safe_next(request))
    response.set_cookie(
        THEME_COOKIE,
        slug,
        max_age=COOKIE_MAX_AGE,
        samesite="Lax",
        httponly=True,
        secure=request.is_secure(),
    )
    return response


def _safe_next(request):
    """The page to go back to: ``next`` if it's on this site, otherwise the home page."""
    target = request.GET.get("next", "/")
    if url_has_allowed_host_and_scheme(
        target, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return target
    return "/"
