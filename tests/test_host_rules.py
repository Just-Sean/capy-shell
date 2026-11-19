"""A rule a module keeps so it fits any project that installs it, such as projects made
from capy-project: it never adds a `check --deploy` warning to the project. (Its
templates are checked in test_csp.py.)"""

import string

from django.core.management import call_command

# A production project's security settings, as capy-project sets them, so any warning
# `check --deploy` still gives comes from the module.
PRODUCTION_SECURITY = {
    "DEBUG": False,
    "SECRET_KEY": "deploy-check-only-" + string.ascii_letters,  # long and varied, not a secret
    "ALLOWED_HOSTS": ["example.com"],
    "SECURE_SSL_REDIRECT": True,
    "SECURE_HSTS_SECONDS": 31536000,
    "SECURE_HSTS_INCLUDE_SUBDOMAINS": True,
    "SECURE_HSTS_PRELOAD": True,
    "SESSION_COOKIE_SECURE": True,
    "CSRF_COOKIE_SECURE": True,
    "X_FRAME_OPTIONS": "DENY",
}
CLICKJACKING_MIDDLEWARE = "django.middleware.clickjacking.XFrameOptionsMiddleware"


def test_the_module_adds_no_deployment_warning(settings):
    for name, value in PRODUCTION_SECURITY.items():
        setattr(settings, name, value)
    settings.MIDDLEWARE = [*settings.MIDDLEWARE, CLICKJACKING_MIDDLEWARE]
    # Raises (and fails the test) on any warning, naming it.
    call_command("check", "--deploy", "--fail-level", "WARNING")
