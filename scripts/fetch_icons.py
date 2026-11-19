"""Vendor the Lucide icons that capy-shell ships.

Downloads a pinned set of Lucide SVGs plus Lucide's license, normalizes each icon
(drops the root ``width``/``height``/``class`` so the ``{% icon %}`` tag controls
them, keeps ``stroke="currentColor"`` so they take the theme's color), and writes
them to ``src/capy_shell/icons/``. Re-run to update the pin or add an icon, then
commit the result. From the repo root:

    uv run python scripts/fetch_icons.py

Lucide is ISC-licensed; its license ships next to the icons as ``LICENSE``.
"""

from __future__ import annotations

import re
import time
import urllib.error
import urllib.request
from pathlib import Path

# Pin the Lucide release the icons are vendored from. Bump this to update them.
LUCIDE_VERSION = "0.545.0"
HOST = "raw.githubusercontent.com"
BASE_PATH = f"/lucide-icons/lucide/{LUCIDE_VERSION}"

# The curated starter set. Add a name here and re-run to vendor more.
ICONS = [
    "menu",
    "x",
    "chevron-down",
    "chevron-right",
    "house",
    "settings",
    "user",
    "log-in",
    "log-out",
    "external-link",
]

OUT_DIR = Path(__file__).resolve().parent.parent / "src" / "capy_shell" / "icons"

# Root-<svg> attributes the tag owns, stripped from each vendored icon.
_DROP_ATTRS = re.compile(r'\s+(?:width|height|class)="[^"]*"')
_SVG_OPEN = re.compile(r"<svg\b[^>]*>", re.IGNORECASE)


def fetch(path: str, attempts: int = 4) -> bytes:
    """GET an HTTPS path from the pinned Lucide host (honors HTTPS_PROXY).

    Retries with backoff: downloads through a proxy can time out transiently.
    """
    url = f"https://{HOST}{path}"
    request = urllib.request.Request(url, headers={"User-Agent": "capy-shell-fetch-icons"})
    last_error: OSError | None = None
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 (pinned HTTPS host, read-only)
                if response.status != 200:
                    raise RuntimeError(f"HTTP {response.status} for {url}")
                return response.read()
        except urllib.error.HTTPError:
            raise  # A 4xx/5xx (e.g. a wrong icon name) won't fix on retry.
        except OSError as error:  # URLError and TimeoutError are both OSError
            last_error = error
            if attempt < attempts - 1:
                time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"Failed to fetch {url} after {attempts} tries: {last_error}")


def normalize(svg: str) -> str:
    """Drop the root width/height/class so the tag controls size and classes."""
    match = _SVG_OPEN.search(svg)
    if match is None:
        raise ValueError("downloaded file is not an <svg>")
    opening = _DROP_ATTRS.sub("", match.group(0))
    return (svg[: match.start()] + opening + svg[match.end() :]).strip() + "\n"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "LICENSE").write_bytes(fetch(f"{BASE_PATH}/LICENSE"))
    for name in ICONS:
        svg = fetch(f"{BASE_PATH}/icons/{name}.svg").decode("utf-8")
        (OUT_DIR / f"{name}.svg").write_text(normalize(svg), encoding="utf-8")
        print(f"vendored {name}.svg")
    print(f"Done: {len(ICONS)} icons from Lucide {LUCIDE_VERSION} -> {OUT_DIR}")


if __name__ == "__main__":
    main()
