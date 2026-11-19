# Capy Shell

App shell — navigation and page chrome — for the capy ecosystem.

A self-contained Django app (`capy_shell`) that any project can install, built
for projects from the capy-project template (v1; called django-starter up to v1.0.1)
and working in any Django project. It has no project of its own: its tests run against
a tiny stand-in project in `tests/`.

**Works with:** Python 3.14+, Django 6.1 or a later 6.x, and PostgreSQL 18 (what
projects made from capy-project run) or SQLite. CI tests both databases with the versions in
`uv.lock` (the newest 6.x), and SQLite once more with the lowest versions allowed
(Django 6.1).

## Architecture

- **The app** (`src/capy_shell/`) is what projects install. Describe its main
  parts here as they grow (models, views, templates, background jobs): what each one
  does, how they connect, and why each major choice was made.
- **The stand-in project** (`tests/settings.py`, `tests/urls.py`) is the smallest
  Django project that runs the app, so the tests prove it works outside any one
  project. `tests/` also checks the rules below.
- **Released as git tags** (`vX.Y.Z`) that projects install from GitHub, never on the
  public PyPI (`pyproject.toml` refuses an upload). Built with uv's own build backend,
  kept up to date with capy-module by Copier (see
  [Updating from the starter](#updating-from-the-starter)).

## Add it to a project

In a project made from capy-project, with its database running
(`docker compose up -d`):

1. Install a released version (a tag) from GitHub; the module's first one is `v0.1.0`:

   ```bash
   uv add git+https://github.com/Just-Sean/capy-shell --tag vX.Y.Z
   ```

   If the repository is private, your machine needs a GitHub login for git (for
   example `gh auth setup-git`), and the project's production image needs one while it
   builds: see "Adding a reusable app" in the project's README (a Docker build
   secret; never a token in the URL). While developing the module next to a project,
   `uv add --editable ../capy-shell` uses your working copy instead. Before
   deploying, run the `uv add … --tag vX.Y.Z` line again: a folder outside the project
   can't be built into its image.

2. Add `"capy_shell"` to `INSTALLED_APPS` in `config/settings/core.py`, in the
   "your apps" part at the top.
3. If the module has URLs, include them in `config/urls.py` (and change its import to
   `from django.urls import include, path`):
   `path("capy-shell/", include("capy_shell.urls"))`.
4. If the module has settings (see [Settings](#settings)), put them in the project's
   settings topic file they belong to, read from the environment, and list each new
   variable in `.env.example`. A new topic file goes in two places in
   `config/settings/__init__.py` (the `from . import …` line and the `for _topic in …`
   list) and in `TOPICS` in `tests/test_settings_package.py`.
5. The module's pages extend the project's `templates/layout.html` (see
   [Pages](#pages)), which shows Django's messages ("Saved.") in a `role="status"`
   region that modules rely on.
   - **A project made from capy-project v1.1.0 or later** already has it: nothing to
     do.
   - **A project made from v1.0.x** (when it was called django-starter): run
     `copier update` to capy-project v1.1.0 or later, which adds `layout.html`, and
     follow the "New in v1.1.0" update notes in capy-project's own README (on its
     GitHub page; a project's README doesn't have them). If you can't update yet, add
     this `templates/layout.html` (your nav bar goes where the comment is; add a
     `footer` block with a `<footer>` once there's something to put in it):

     ```html
     {% extends "base.html" %}
     {% block header %}
     <header>
       {# Your nav bar. #}
       <div role="status">
         {% for message in messages %}<p>{{ message }}</p>{% endfor %}
       </div>
     </header>
     {% endblock %}
     ```

     A theme that sets attributes on `<html>` also needs that project's `base.html`
     to have the `html_attrs` block, as in v1.1.0: change its `<html lang="en">` line
     to `<html lang="en"{% block html_attrs %}{% endblock %}>`.
     Without it, the theme's line is silently ignored. If you added this README's
     earlier `layout.html`, delete its empty `footer` block: an empty `<footer>` is
     announced by screen readers as a landmark with nothing in it.

   If this module is a theme or an app shell, also add the line this README gives to
   the project's `layout.html`, where its comments say (see [Pages](#pages)).
6. Create its tables, then run the project's tests:

   ```bash
   uv run python manage.py migrate      # production's migrate step does this by itself
   uv run pytest
   ```

### Wiring the app shell

capy-shell needs **capy-theme** installed (its header uses `{% theme_logo %}` and
`{% theme_mode_toggle %}`), plus three bits of wiring:

1. Add `"capy_shell.context_processors.shell"` to the template
   `OPTIONS["context_processors"]`.
2. Point the project's `layout.html` at the shell and fill its brand and
   header-action slots (this is the one-line injection step 5 refers to):

   ```html
   {% extends "capy_shell/base.html" %}
   {% load capy_theme %}
   {% block shell_brand %}<a href="/">{% theme_logo %}</a>{% endblock %}
   {% block shell_header_actions %}{% theme_mode_toggle %}{% endblock %}
   ```

   The project's `base.html` must expose a `{% block body %}` inside `<body>`
   (the shell fills it). Feature modules extend `layout.html` and fill
   `{% block content %}`.
3. Add capy-shell's templates to the project's Tailwind `@source`, so the daisyUI
   classes in them are built (adjust the Python version to match):

   ```css
   @source "../.venv/lib/python3.14/site-packages/capy_shell/templates";
   ```

## Running the demo

A dev-only demo site (`demo/`) shows the shell. It installs capy-theme as a sibling
checkout — see `pyproject.toml`'s `[tool.uv.sources]`; adjust the path if yours
differs. From the repo root:

```bash
uv sync --group demo   # installs capy-theme + the Tailwind CLI (demo-only deps)
uv run python demo/manage.py migrate
uv run python demo/manage.py tailwind runserver   # http://localhost:8000/
```

## Settings

Each setting is read with the `CAPY_SHELL_` prefix and a sensible default (see
`conf.py`). capy-shell owns page *structure and geometry*; the *look* (colours,
type, spacing) comes from capy-theme's daisyUI tokens, so there are few here.

| Setting | Default | What it does |
|---|---|---|
| `CAPY_SHELL_CONTENT_MAX_WIDTH` | `"max-w-7xl"` | Tailwind max-width for the content container pages render in, so lines stay readable on wide screens. A page needing full width overrides the container in its own template. |
| `CAPY_SHELL_CONTENT_PADDING` | `"px-4 py-6"` | Tailwind padding for the content container. |
| `CAPY_SHELL_HOME_URL` | `"/"` | Where the header's brand/logo links. |

## Upgrading

Install the new tag (the same `uv add … --tag vX.Y.Z` line), then run
`uv run python manage.py migrate`, and in production deploy as usual (the image runs
`collectstatic`; the migrate step migrates). Read `CHANGELOG.md` first: each version
says what a project must do, if anything. When it says "deploy vX.Y.Z first", install
and deploy that version before going further, even when jumping several versions:
skipping it can remove a column the running code still uses (see
[Database](#database)).

## Logging

The module logs through its own logger, never `print()`, and never sets up handlers
(the project decides where logs go):

```python
import logging

logger = logging.getLogger("capy_shell")
```

Never log secrets, passwords, tokens or personal data; log IDs instead.

## Rules that keep it pluggable

- Never import from a project or from another module.
- Link to users with `settings.AUTH_USER_MODEL`, never a project's `User` class.
- Keep templates in `src/capy_shell/templates/capy_shell/` and static
  files in `src/capy_shell/static/capy_shell/`, so names never clash.
- Read settings with the `CAPY_SHELL_` prefix and a default (see
  Settings), when they're used (in forms, views, validation), never in a model field's
  definition (`choices`, `max_length`, `default`, `upload_to`): a project that changed
  the setting would get migrations of its own for the module.
- **Never add a `check --deploy` warning** to a project (`tests/test_host_rules.py`
  checks this).
- **URLs:** name them inside `app_name = "capy_shell"` in `urls.py`
  (`{% url "capy_shell:detail" … %}`), so
  they never clash with a project's. Models expose a `public_id` (a UUID) in URLs and
  APIs, never the database `id`, as projects made from capy-project do.
- **Business logic** lives in plain functions (`services.py` for changes, `selectors.py`
  for reads) that views, the admin and background jobs share.
- **Slow work** (emails, file processing, calls to other services) goes to a
  background job with Django's Tasks API, in the module's `tasks.py`: enqueue it with
  `transaction.on_commit(lambda: my_job.enqueue(obj.id))` when saving something, keep
  each job well under 60 seconds (a deploy waits that long for running jobs), and when
  a job's arguments change, keep accepting the old ones until queued jobs have run. A
  project needs its `worker` running for them. **Email** goes through
  `django.core.mail`.
- **The cache** is Redis in projects made from capy-project, and Django raises an error when
  Redis is down: code that must keep working then catches cache errors and falls back
  to the database. Clear a cached value when its data is saved; don't rely on a
  timeout alone.

### Pages

- **Every page extends `layout.html`**, the project's own layout (its nav bar, theme
  and any footer), and fills only:
  - `{% block title %}`: always, with what the page is ("Edit
    invoice"), translated like other text. Without it the tab says "Untitled page",
    which screen readers announce.
  - `{% block head %}{{ block.super }}…{% endblock %}`: the page's
    stylesheets and scripts, starting with `{{ block.super }}`.
  - `{% block content %}`: the page itself.

  Leave `header` and `footer` to the project, and never ship a `layout.html` of your
  own. A module whose job is the layout itself (a nav menu, a theme) provides template
  tags instead, and its README says which line a project adds to its `layout.html`:
  in its `head` block, in the nav in its `<header>`, or, for attributes on `<html>`,
  in its `html_attrs` block, starting with a space
  (`{% block html_attrs %} data-theme="dark"{% endblock %}`), since
  it follows `lang="en"`.
  Modules rely only on the name `layout.html`, these three blocks, and the layout
  showing Django's messages in a `role="status"` region. Template tags that
  read the database belong in `layout.html`, never in `base.html`, so the project's
  error pages keep working when the database is down; a tag shown on every page runs a
  fixed, small number of queries.
- **Accessible** (WCAG 2.2 AA):
  - the content starts with one `<h1>`, headings in order;
  - no page-level `<main>`, `<header>` or `<footer>` of the module's own (the layout
    has them; a `<header>` inside an `<article>` is fine);
  - forms rendered by Django (labels, help text and errors linked to their fields) or,
    when written by hand, a visible `<label for>` and `aria-describedby` for help and
    errors on every field; after a failed submit, the errors are near the top of the
    page or the first wrong field gets the focus;
  - real `<button>` and `<a>` elements, never clickable `<div>`s; buttons and
    standalone links (not links inside a sentence) at least 24 by 24 CSS
    pixels, with a visible focus outline (never `outline: none` without a replacement);
  - every `<img>` has `alt` (empty, `alt=""`, for decoration) and its `width` and
    `height`, so the page doesn't jump while it loads;
  - the module's CSS uses the page's colors (`currentColor`, inherited colors or the
    theme's CSS variables) rather than fixed ones, and any color it does set has enough
    contrast (4.5:1 for text, 3:1 for icons and borders) in both light and dark mode;
  - sizes in `rem`, and the page works at 320 px wide and zoomed to 200% without
    scrolling sideways;
  - animations and transitions stop under `@media (prefers-reduced-motion: reduce)`.
- **Static files** always through `{% load static %}{% static "capy_shell/…" %}`,
  never `/static/…` (projects give files cache-busting names). `url()` paths in CSS
  are relative and must exist (the project's `collectstatic` fails otherwise). Scripts
  get `defer`; no web fonts of the module's own.
- **Text people see** is marked for translation: `gettext_lazy as _` in Python
  (models' `verbose_name`, form labels, messages) and
  `{% load i18n %}{% translate "…" %}` in templates
  (`{% blocktranslate %}…{{ name }}…{% endblocktranslate %}` for text
  with values in it).
- **Confirm actions** with Django's messages framework
  (`messages.success(request, _("Saved."))`); the project's `layout.html` shows them.
- **No inline code**: projects enforce a strict Content Security Policy (a
  project made from capy-project only reports problems while you develop, and blocks them in
  production). Put CSS and JavaScript in static files; if inline code is unavoidable,
  give the tag `nonce="{{ csp_nonce }}"` or
  `{% csp_nonce_attr %}`. Never `style="…"`, `onclick=` or
  `javascript:` links, and no code that needs `eval` (htmx's `hx-on`, or Alpine's
  standard build: use its CSP build). Load nothing from other sites (CDNs, web fonts, images too) and don't post
  forms to them; `data:` URLs only for images and icons. No frames, video, audio,
  embedded objects or manifests: the policy of projects made from capy-project blocks them all.
- **`tests/test_csp.py` checks** the module's HTML, SVG, XML and Jinja templates under
  `templates/` and `jinja2/` against that policy. It's a safety net that reads
  template source, not a browser: it can't see CSS or JavaScript files, what inline
  code loads, what template variables hold (a URL from a setting or the database), a
  block a project's template fills in, HTML built in Python (`format_html`), or
  markup opened in one `{% if %}` branch and closed in another, so
  keep the same rules there. It reports a full URL to the project's own site as another
  site (use a path, `/x/`, or `{% url %}`), and a nonce'd script
  whose code contains the text `<script` or `<style`. To comment code out, use
  `{% comment %}`, a one-line `{# #}` or an
  HTML comment: Django prints a `{# #}` that spans lines as text,
  and the check reads Jinja templates the same way, so keep `{# #}`
  on one line in Jinja templates too.
- **HTML emails** go in `templates/capy_shell/emails/` (or
  `jinja2/capy_shell/emails/`): they need inline styles and full image URLs,
  and the site's policy doesn't apply to them, so the check skips that folder. Nothing
  else goes there.
- **Testing pages:** the stand-in project has no `layout.html`. When the module gets
  pages, add `"DIRS": [Path(__file__).parent / "templates"]` (with
  `from pathlib import Path`) to `TEMPLATES` in `tests/settings.py`, and a
  `tests/templates/layout.html` shaped like a project's:

  ```html
  <!doctype html>
  <html lang="en"{% block html_attrs %}{% endblock %}>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    {% block head %}{% endblock %}
    <title>{% block title %}Untitled page{% endblock %}</title>
  </head>
  <body>
    <header>
      <div role="status">
        {% for message in messages %}<p>{{ message }}</p>{% endfor %}
      </div>
    </header>
    <main id="main">{% block content %}{% endblock %}</main>
  </body>
  </html>
  ```

## Security

Rules for the module's code. The project trusts whatever the module does, so:

- **Views:** every view checks login and permission (or ownership), so nobody can see
  or change someone else's data by changing an ID in the URL. Test it for anonymous
  users and for other users.
- **Forms and input:** validate all input with Django forms;
  `{% csrf_token %}` in every POST form; never `csrf_exempt`.
- **Database:** the ORM or parameterized queries only, never SQL built from strings.
- **Changes only on POST:** a view that changes anything refuses GET
  (`@require_POST`), so a link or an image on another site can't trigger it. Check
  redirect targets such as `next` with `url_has_allowed_host_and_scheme` (no open
  redirects).
- **Logins:** never check passwords or tokens yourself; use
  `django.contrib.auth.authenticate(request, ...)`, so the project's login rate
  limiting (django-axes) counts every attempt.
- **Output:** keep auto-escaping; never `|safe` or `mark_safe` on anything a user
  typed. Auto-escaping only makes text safe inside HTML, not inside CSS, JavaScript or
  a URL, so:
  - a value that ends up in CSS, JavaScript or a URL (a color, a name, a link) is
    checked against a strict pattern or a list of choices when it's saved, not only
    when it's shown;
  - data for JavaScript goes through `{{ data|json_script:"id" }}`,
    never `{{ }}` inside a script;
  - never build a `Template(...)` from text a user typed;
  - a URL a user gives is saved and put in a link (`href`) only if it starts with
    `https://` (or `http://`): this stops `javascript:` links. Never redirect to one;
    redirects go only to pages on the project's own site (see `next` above).
- **Uploads:** check the size, and the type from the file's content, never from its
  name or the browser's word. For images, during the request, keeping Pillow's
  `MAX_IMAGE_PIXELS` limit and treating its `DecompressionBombWarning` as an error
  (only around this check, not for the whole server):

  ```python
  import warnings

  from PIL import Image

  with warnings.catch_warnings():
      warnings.simplefilter("error", Image.DecompressionBombWarning)
      with Image.open(upload) as img:
          img.verify()  # raises for a broken or oversized image: refuse the upload
          kind = img.format  # e.g. "PNG": check it's one the module allows
  ```

  Fully decoding, resizing or converting an image happens later, in a background job
  (see below).
  Name the stored file's extension after the format Pillow found (`img.format`), not
  the uploaded name. `ImageField` needs Pillow (`uv add pillow`). Store each file
  under a `capy_shell/` folder with a random part, from a function of the
  module's own (projects' helpers can't be imported):

  ```python
  from uuid import uuid4

  from django.utils.text import get_valid_filename


  def random_folder(instance, filename):
      # Each file in its own unguessable folder; a top-level function keeps migrations stable.
      return f"capy_shell/{uuid4().hex}/{get_valid_filename(filename)}"
  ```

  In projects made from capy-project the default storage is **private**: its files are served
  only through the project's own view, to whoever the project's `can_download()`
  allows (by default, active staff). So a module that keeps private files either says
  in this README what projects should allow in `can_download()`, or serves them
  through its own view that checks permission. Such a view sends each file with
  `FileResponse(…, as_attachment=True)` and the headers
  `X-Content-Type-Options: nosniff`, `Content-Security-Policy: default-src 'none'; sandbox`
  and `Cache-Control: private, no-store`, always as a download, as the project's own
  view does (an `<img>` tag still shows an image sent this way). With S3 storage
  (`DJANGO_MEDIA_STORAGE=s3`), a file's `.url` is a signed link that works for an hour
  for whoever has it: show it only to people allowed to see the file, and never save
  or email it. Files anyone may see (pictures on public pages) go in the project's
  "public" storage, chosen without importing project code (a function keeps the
  module's migrations the same in every project):

  ```python
  from django.conf import settings
  from django.core.files.storage import default_storage, storages


  def public_storage():
      # The project's public storage (capy-project's projects have one), else the default.
      return storages["public"] if "public" in settings.STORAGES else default_storage
  ```

  and `models.ImageField(storage=public_storage, upload_to=random_folder, ...)`.
  Unpacking archives, decoding images or reading fonts is capped in size and runs in a
  background job, never in the request.
- **URLs a user gives** (webhooks, "import from a link", remote images): otherwise a
  user can make the server reach its own database, Redis, cloud metadata or other
  internal services. Fetch them in a background job, and:
  - only `https://` on port 443;
  - resolve the host, and go on only if **every** address it gives is public
    (`ipaddress.ip_address(a).is_global`; for an IPv6 address, check its
    `ipv4_mapped` address too);
  - connect to the address you checked, not the name again: a second lookup can give
    a different, internal address (DNS rebinding). Keep certificate checks on, checked
    against the original host name (the client library's way of pinning the address
    while keeping the name, never `verify=False`);
  - don't follow redirects, or check each one the same way;
  - cap the response size and the time.
- **Background jobs:** pass IDs, never secrets, tokens or personal data, as arguments:
  they're stored in the database and shown in the admin.
- **Secrets:** never in code. A secret the module needs comes from a project setting
  (read from the environment there); fail with a clear error if it's missing.
- **Calls to other services:** HTTPS only, certificate checks on, and a timeout.
- **Logs:** see [Logging](#logging).

## Database

- **Supported:** PostgreSQL 18 and SQLite (both tested on every pull request). CI's
  Postgres tests log in as a role like the app login of a project made from capy-project (not a
  superuser), as projects migrate with.
- **Every migration keeps working with the previous release's code.** Projects
  migrate while the old code still runs, and a rollback keeps the new database with
  the old code, so:
  - a new field is `null=True` or has `db_default=…`, never only `default=` (which
    exists only in Python: the old code's inserts would fail);
  - a new constraint accepts every row the previous release can write;
  - a model gets its `public_id` in the migration that creates it: adding a unique
    field to a table that already has rows rewrites and locks the whole table (it then
    takes a nullable field, filled in batches, and a unique index made as below);
  - **removing a field takes three releases:**
    1. stop using it, and make it nullable or give it a `db_default`;
    2. remove it from the model with a migration that changes only Django's state
       (`migrations.SeparateDatabaseAndState(state_operations=[migrations.RemoveField(…)])`,
       no database operations);
    3. drop the column. Django's `RemoveField` can't (the field is no longer in the
       model), so use
       `migrations.RunSQL('ALTER TABLE "capy_shell_thing" DROP COLUMN "old_name"', migrations.RunSQL.noop)`
       (on SQLite, the column's index or constraint must go first), or `DROP TABLE`
       for a whole model.
  - **renaming a field** the same way, or its data is lost (the old code keeps writing
    only the old column, during the deploy and after a rollback):
    1. add the new field (nullable or with a `db_default`), write to both fields, and
       copy the old values across in a data migration;
    2. copy again the rows the old code wrote meanwhile, make the old field nullable
       (or give it a `db_default`), read and write only the new field, and remove the
       old one from the model (state only);
    3. drop the old column.

    If the new field must be required, make it so in a later release, after step 2's
    copy. Each of these releases can be rolled back only to the one before it, and the
    column drop can't be undone.

    To rename it only in Python, keep the column instead:
    `new_name = models.CharField(…, db_column="old_name")` changes nothing in the
    database.
- **A release that finishes such a change** says "deploy vX.Y.Z first" in
  `CHANGELOG.md`, naming the release before it, so a project that skips versions
  doesn't drop a column its running code still uses (see [Upgrading](#upgrading)).
- **Big tables:** on Postgres, a plain `AddIndex`, a field type change and a new
  unique, check or foreign-key constraint lock the table for as long as they take,
  while the old code is serving; a new foreign key locks the table it points to (often
  the users table) too, and every query that comes after a waiting migration waits
  as well. Build indexes with `CONCURRENTLY`, which doesn't lock. Django's
  `AddIndexConcurrently` crashes on SQLite, so a module that supports both uses a
  migration like this one:

  ```python
  from django.db import migrations, models

  # The name is unique in the whole database, 30 characters at most.
  INDEX = models.Index(fields=["created"], name="capy_shell_created_idx")


  def add_index(apps, schema_editor):
      model = apps.get_model("capy_shell", "Thing")
      if schema_editor.connection.vendor == "postgresql":
          schema_editor.add_index(model, INDEX, concurrently=True)
      else:
          schema_editor.add_index(model, INDEX)


  def remove_index(apps, schema_editor):
      model = apps.get_model("capy_shell", "Thing")
      if schema_editor.connection.vendor == "postgresql":
          schema_editor.remove_index(model, INDEX, concurrently=True)
      else:
          schema_editor.remove_index(model, INDEX)


  class Migration(migrations.Migration):
      atomic = False  # CONCURRENTLY can't run inside a transaction

      dependencies = [("capy_shell", "0002_previous")]

      operations = [
          migrations.SeparateDatabaseAndState(
              database_operations=[migrations.RunPython(add_index, remove_index)],
              state_operations=[migrations.AddIndex("thing", INDEX)],
          ),
      ]
  ```

  Add the same index to the model's `Meta.indexes`. If the migration fails on
  Postgres, it leaves an INVALID index behind: drop it (`DROP INDEX CONCURRENTLY …`)
  before running `migrate` again.
- **Data migrations** that change many rows go in a migration of their own (never with
  schema changes), with `atomic = False`, saving each batch (say 1,000 rows) in its own
  `transaction.atomic()`, so no single transaction holds the table for long.
- **Nothing that needs a superuser** (e.g. `CREATE EXTENSION` of an untrusted
  extension; trusted ones such as `pg_trgm` work): projects made from capy-project migrate
  with a login that isn't one, and so does CI. If the module needs such an extension,
  say so here and in the CHANGELOG, so the project adds it first.
- **Never edit or delete a released migration**; add a new one. Data migrations use
  `apps.get_model` and have a reverse (or `migrations.RunPython.noop`).
- **Queries:** no query per row (`select_related` and `prefetch_related`); an index for
  the filters and orderings the module runs often on tables that grow (each index slows
  every write, so not on every field); pagination on any list that grows; and in the
  admin, `raw_id_fields` for links to users (`autocomplete_fields` only works if the
  project's user admin has `search_fields`) or other big tables, since a plain one
  puts every user in the page. pytest-django's `django_assert_max_num_queries` keeps a
  page's query count in check in its tests.
- **Say in the CHANGELOG** when a migration deletes data or is slow on big tables.

Create migrations after changing models (`tests/test_app.py` fails until you do):

```bash
uv run django-admin makemigrations capy_shell --settings=tests.settings --pythonpath=.
```

## Develop it

You need git, Docker (for Postgres tests and full secret scans) and uv 0.12: the
module requires that version line, the same one CI uses, so `uv.lock` is always
written the way CI reads it. If uv came from its standalone installer,
`uv self update 0.12.24` switches to it (down from a newer uv too); otherwise install
0.12.24 the way you installed uv. Once, right after making the module:

```bash
git init -b main           # a new module isn't a git repo yet (CI and releases use main)
uv lock                    # pins every package version in uv.lock: commit it (CI needs it)
uv sync                    # installs Python, Django and the test tools
uv run pre-commit install  # turns on the checks that run on every commit
git add -A && git commit -m "Start from capy-module"
```

Then create the repository on GitHub under `Just-Sean`, named
`capy-shell`, public (MIT), and push. With
GitHub's `gh` tool:

```bash
gh repo create Just-Sean/capy-shell --public --source . --push
```

(or create it on github.com, then `git remote add origin
https://github.com/Just-Sean/capy-shell.git` and
`git push -u origin main`). In the repository's Settings:

- **Code security** (called "Advanced Security" on some accounts): turn on
  "Dependabot alerts" and "Dependabot security updates"; for a public repository, also
  secret scanning with push protection, and code scanning.
- **Branches:** protect `main` so a pull request needs CI to pass before it's merged:
  require the checks "Lint (ruff)", "Tests (sqlite, locked versions)", "Tests
  (postgres, locked versions)", "Tests (sqlite, lowest versions)", "Dependency
  vulnerabilities (pip-audit)", "Package (only the module ships)" and "Secrets
  (gitleaks, whole history)". GitHub lists them to pick from only after CI has run
  once, so open your first pull request, then come back. On a free GitHub account,
  a private repository can't protect branches: there, check that CI passed before you
  merge.

Every day:

```bash
uv run pytest                      # runs the tests on SQLite, no setup needed
uv run pytest --cov                # the same, with coverage (fails below 80%)
uv run ruff check .                # finds problems
uv run ruff format .               # formats the code
uv run pre-commit run --all-files  # the commit checks, on every file
```

Before every pull request, check the dependencies for known vulnerabilities:

```bash
(f=$(mktemp) && trap 'rm -f "$f"' EXIT && uv export --locked --format requirements-txt --no-emit-project --quiet -o "$f" && uv run pip-audit --disable-pip --require-hashes -r "$f")
```

**On GitHub,** every pull request runs `.github/workflows/ci.yml`: ruff; the tests
with coverage on SQLite and on PostgreSQL 18 (logged in as a role that isn't a
superuser, like a project's) with the versions in `uv.lock`, and once more on SQLite
with the lowest versions `pyproject.toml` allows; pip-audit; a scan of the whole
history for secrets (gitleaks); and a check that the built package holds only the
module. A newer push to a pull request cancels the older run. Dependabot
(`.github/dependabot.yml`) opens pull requests for updates every week, once a release
is a week old.

The commit check only scans what's being committed. To scan every file and the whole
history for secrets (the every-file scan also reads files git ignores, like a local
`.env`, so a finding there may never have been committed):

```bash
docker run --rm -v "$PWD:/repo:ro" ghcr.io/gitleaks/gitleaks:v8.30.1@sha256:c00b6bd0aeb3071cbcb79009cb16a60dd9e0a7c60e2be9ab65d25e6bc8abbb7f dir /repo --redact   # every file
docker run --rm -v "$PWD:/repo:ro" ghcr.io/gitleaks/gitleaks:v8.30.1@sha256:c00b6bd0aeb3071cbcb79009cb16a60dd9e0a7c60e2be9ab65d25e6bc8abbb7f git /repo --redact   # the whole history
```

**Updated by hand** (Dependabot doesn't touch these), keeping each pair in step:

- **uv:** `UV_VERSION` in `.github/workflows/ci.yml`, and in `pyproject.toml` both
  `required-version` and the `uv_build` range (`>=0.12,<0.13` goes with uv 0.12),
  plus the `uv self update` command under Develop it.
- **gitleaks:** `rev` in `.pre-commit-config.yaml` (`uv run pre-commit autoupdate --freeze`)
  and `GITLEAKS_IMAGE` in `.github/workflows/ci.yml`, plus the two commands above.

To run the tests on Postgres here too, with a login like CI's (port 5433, so it never
clashes with a project's database on 5432):

```bash
docker run -d --rm --name capy-shell-postgres -p 127.0.0.1:5433:5432 -e POSTGRES_USER=app -e POSTGRES_PASSWORD=app -e POSTGRES_DB=module_tests postgres:18-trixie
docker exec capy-shell-postgres pg_isready -U app -h 127.0.0.1   # repeat until "accepting connections"
docker exec capy-shell-postgres psql -U app -d module_tests -c "CREATE ROLE module LOGIN PASSWORD 'module' NOSUPERUSER CREATEDB"
DATABASE_URL=postgres://module:module@localhost:5433/module_tests uv run pytest
docker stop capy-shell-postgres   # stops it and deletes it, data included
```

To check what the package will ship (CI does this too): `rm -rf dist && uv build
--wheel`, then `uv run python -m zipfile -l dist/*.whl` should list only
`capy_shell/` and its metadata.

## Release a version

After the first push, nothing is pushed straight to `main`: every change goes
through a pull request. Each tag is `v` plus `version` from `pyproject.toml`.

**The first release** is `v0.1.0`: `pyproject.toml` and `CHANGELOG.md` already say
0.1.0. If the CHANGELOG's 0.1.0 entry needs more, follow steps 1 to 4 without changing
the version. If not, there's nothing for a pull request: check that CI passed on
`main`, try `main` in a project as step 2 says (with `--branch main`), then tag `v0.1.0` (step 4).

1. Open an issue for the release and a branch for it. Change `version` in
   `pyproject.toml`, run `uv lock` (CI refuses a lock file that doesn't match), and add
   the version at the top of `CHANGELOG.md`: what changed, and what a project must do
   when it upgrades (newest version first). Commit `pyproject.toml`, `uv.lock` and
   `CHANGELOG.md`.
2. Try the branch in a project made from capy-project:
   - **While developing:** install your working copy
     (`uv add --editable ../capy-shell`) and run the project's tests (they
     include `check --deploy` with production settings).
   - **In production form:** push the branch, install it with
     `uv add git+https://github.com/Just-Sean/capy-shell --branch BRANCH`,
     and try it in the project's local production run (its README, "Production (the
     real image, run locally)").

   Afterwards, put the project back on its previous tag (the `uv add … --tag` line),
   or `uv remove capy-shell` before the module's first release.
3. Open a pull request; CI must pass (both databases, the lowest versions, the package
   check). Merge it.
4. Tag the merged `main` and push only the tag:

   ```bash
   git switch main && git pull
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

5. In each project, install the new tag when you want it (see [Upgrading](#upgrading)).

## Updating from the starter

When capy-module improves (its release notes on GitHub say what changed and
what to do):

1. Commit everything, and make a branch.
2. Run `copier update`. Copier asks its questions again: press Enter to keep each
   answer.
3. Where the starter and your module both changed a file, Copier writes both versions
   into it between `<<<<<<<` and `>>>>>>>` lines: search for `<<<<<<<` (`git status`
   lists the changed files) and keep the right lines, your own changes and the newer
   of two pinned versions.
4. Run `uv lock`, `uv run pytest --cov` and `uv run ruff check .`.
5. Commit, open a pull request, and merge it once CI passes. If CI's check names
   changed, update the required checks under Settings > Branches.

To change the GitHub owner (or the license or copyright year) the module was made
with, which also brings in the starter's newest release as `copier update` always
does:

```bash
copier update --defaults --data github_owner=NEW-OWNER
```

If the repository itself moved, also point git at it:
`git remote set-url origin https://github.com/NEW-OWNER/capy-shell.git`.

## Files

| Path | Purpose |
| --- | --- |
| `src/capy_shell/` | The Django app that projects install |
| `src/capy_shell/apps.py` | The app's name, label and admin title |
| `src/capy_shell/models.py` | Database models (empty to start) |
| `src/capy_shell/migrations/` | Database migrations (see Database) |
| `tests/settings.py` | A tiny stand-in project for the tests |
| `tests/urls.py` | The stand-in project's URLs; add the module's here once it has some |
| `tests/test_app.py` | Checks the app loads from its own package and its migrations are complete |
| `tests/test_host_rules.py` | Checks the module adds no `check --deploy` warning to a project |
| `tests/test_csp.py` | Checks the module's templates have nothing a strict Content Security Policy blocks |
| `LICENSE` | The module's license (MIT) |
| `pyproject.toml` | Package name, version, Django versions supported, tool settings |
| `CHANGELOG.md` | What changed in each version, and what projects must do |
| `uv.lock` | The exact version of every package, so tests and CI install the same thing (commit it) |
| `.pre-commit-config.yaml` | The checks on every commit: gitleaks (secrets) and ruff |
| `.github/workflows/ci.yml` | The checks on every pull request (see Develop it) |
| `.github/dependabot.yml` | Weekly pull requests for package and CI updates |
| `.gitignore` | Keeps secrets, keys, local databases and test output out of git |
| `.python-version` | The Python version uv installs |
| `.copier-answers.yml` | Lets `copier update` find the template; don't edit |

## License

MIT: see `LICENSE`.
