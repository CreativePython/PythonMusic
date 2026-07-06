"""MkDocs hook: fill in the latest GitHub release's version and date.

Any page can write the placeholders %%version%% and %%date%%; this hook swaps
them for the tag name and publish date of the most recent release of the
PythonMusic repo (e.g. download.md's "(v1.2.0 - July 6, 2026)" line). That way
the download page never quotes a stale version number by hand.

The release info is fetched from GitHub's API once per process and cached, so
live-reload during `mkdocs serve` doesn't hammer the API. If you publish a new
release mid-serve, restart serve to pick it up; `build` and `gh-deploy` always
start fresh.

If GitHub can't be reached (offline, rate-limited, etc.) we log a warning and
leave the placeholders untouched rather than fail the build.
"""

import json
import logging
import urllib.request
from datetime import datetime

_LATEST_RELEASE_API = "https://api.github.com/repos/ydhadix/PythonMusic/releases/latest"

log = logging.getLogger("mkdocs.hooks.release_info")

# Cached (version, date) strings, looked up once per process.
_release_info = None


def _fetch_release_info():
    """Return (version, date) for the latest release, or None if unavailable."""
    request = urllib.request.Request(
        _LATEST_RELEASE_API,
        headers={"Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        release = json.load(response)

    version = release["tag_name"]

    # published_at looks like "2026-07-06T18:30:00Z"; show it as "July 6, 2026".
    published = datetime.strptime(release["published_at"], "%Y-%m-%dT%H:%M:%SZ")
    date = f"{published:%B} {published.day}, {published.year}"

    return version, date


def on_page_markdown(markdown, page, config, files):
    # Nothing to do unless this page actually uses one of the placeholders.
    if "%%version%%" not in markdown and "%%date%%" not in markdown:
        return markdown

    global _release_info
    if _release_info is None:
        try:
            _release_info = _fetch_release_info()
        except Exception as error:
            log.warning("Could not fetch the latest GitHub release: %s", error)
            return markdown

    version, date = _release_info
    markdown = markdown.replace("%%version%%", version)
    markdown = markdown.replace("%%date%%", date)
    return markdown