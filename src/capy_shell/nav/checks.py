"""A Django system check so an invalid module nav fails at ``manage.py check`` and at
boot (deploy), not at render time in front of an end user."""

from __future__ import annotations

from django.core.checks import Error
from django.core.checks import register as register_check

from .collect import collect
from .schema import NavError

NAV_ERROR_ID = "capy_shell.E001"


def check_nav(app_configs, **kwargs):
    """Collect the nav and report any invalid declaration as a check error."""
    try:
        collect()
    except (NavError, ImportError) as error:
        return [
            Error(
                f"A module declares invalid nav: {error}",
                hint="Fix the offending app's nav.py (see capy-shell's Navigation docs).",
                id=NAV_ERROR_ID,
            )
        ]
    return []


def register():
    """Register the nav system check. Called from CapyShellConfig.ready()."""
    register_check(check_nav)
