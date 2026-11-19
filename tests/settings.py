"""The smallest Django project that can run this module's tests.

It stands in for "any project that installs the module". If the module only
works inside one particular project, these tests fail.

Database: SQLite in memory by default, no setup needed. To test against
Postgres (for Postgres-only features), set DATABASE_URL (the README's "Develop it"
starts this database, with a login like CI's):
    DATABASE_URL=postgres://module:module@localhost:5433/module_tests uv run pytest
"""

import os
import secrets
from pathlib import Path

import dj_database_url

SECRET_KEY = secrets.token_urlsafe(50)  # a new one every run: nothing to keep secret
DEBUG = False
ALLOWED_HOSTS = ["testserver"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "capy_shell",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "tests.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [Path(__file__).parent / "templates"],  # the stand-in project's base.html
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "capy_shell.context_processors.shell",
            ],
            # capy-theme isn't installed here (or in CI), so stand its template tags
            # in with no-ops, letting the shell's templates render in the tests.
            "libraries": {"capy_theme": "tests.capy_theme_stub"},
        },
    },
]

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite://:memory:")
DATABASES = {"default": dj_database_url.parse(DATABASE_URL)}

USE_TZ = True
STATIC_URL = "static/"
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]  # fast tests
