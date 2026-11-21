"""The shell's views: remembering the visitor's theme choice for each scheme."""

from django.http import Http404, HttpResponseRedirect
from django.utils.http import url_has_allowed_host_and_scheme

from .context_processors import DARK_COOKIE, LIGHT_COOKIE

COOKIE_MAX_AGE = 60 * 60 * 24 * 365  # a year, so the choice survives closing the browser
SCHEME_COOKIE = {"light": LIGHT_COOKIE, "dark": DARK_COOKIE}


def set_theme(request, scheme, slug):
    """Remember the visitor's chosen theme (its slug) for one scheme, then go back.

    A plain link, so the picker works without JavaScript. ``scheme`` is "light" or "dark".
    The slug isn't validated here: the theme_slots tag ignores a pick that isn't a theme
    of that scheme in capy-theme's catalog and falls back to the admin's default theme.
    """
    cookie = SCHEME_COOKIE.get(scheme)
    if cookie is None:
        raise Http404("Unknown scheme.")
    response = HttpResponseRedirect(_safe_next(request))
    response.set_cookie(
        cookie,
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
