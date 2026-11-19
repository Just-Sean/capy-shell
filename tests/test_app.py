"""Checks every module should keep passing."""

from io import StringIO
from pathlib import Path

import pytest
from django.apps import apps
from django.core.management import call_command

PACKAGE = "capy_shell"
VERBOSE_NAME = "Capy Shell"
SRC_DIR = Path(__file__).resolve().parent.parent / "src"


def test_app_is_installed():
    assert apps.get_app_config(PACKAGE).verbose_name == VERBOSE_NAME


def test_app_loads_from_its_own_package():
    # A module named like a Python standard-library module (json, email, ...) or like
    # the tests folder would load that instead, and the other tests could still pass.
    config = apps.get_app_config(PACKAGE)
    assert type(config).__module__ == f"{PACKAGE}.apps"
    assert Path(config.path) == SRC_DIR / PACKAGE


@pytest.mark.django_db
def test_migrations_are_up_to_date():
    # Fails if a model changed without `makemigrations`, which would break every
    # project that installs this version. The message says which migration is missing.
    output = StringIO()
    try:
        call_command(
            "makemigrations", PACKAGE, "--check", "--dry-run", stdout=output, stderr=output
        )
    except SystemExit:
        pytest.fail(
            f"Missing migrations; run makemigrations (see the README):\n{output.getvalue()}"
        )
