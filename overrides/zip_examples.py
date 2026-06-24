"""MkDocs hook: bundle the example snippets into a downloadable archive.

We zip the whole examples/_snippets folder into a single
examples/PythonMusic_Examples.zip so download.md can link to one archive of
every chapter's example. The zip is generated in memory and registered as a
MkDocs "generated" file, so it never goes stale and no binary is committed.

Registering it in on_files (rather than writing to site/ in on_post_build) is
what keeps MkDocs happy: the file is known before link validation runs, so the
download link no longer reports a missing target during `mkdocs serve`.

To avoid rebuilding the archive on every live-reload during `serve`, the zip
bytes are built once per process and cached. If you edit a snippet mid-serve,
restart serve to refresh the archive (it was never refreshed during serve
before either); `build` and `gh-deploy` always start fresh.
"""

import io
import zipfile
from pathlib import Path

from mkdocs.structure.files import File

_ARCHIVE_URI = "examples/PythonMusic_Examples.zip"

# Cached zip bytes, built once per process so serve's live-reload doesn't re-zip.
_archive_bytes = None


def _build_zip_bytes(snippets_dir: Path) -> bytes:
    """Zip every file under snippets_dir, with paths relative to it."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(snippets_dir.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(snippets_dir))
    return buffer.getvalue()


def on_files(files, config):
    global _archive_bytes
    if _archive_bytes is None:
        snippets_dir = Path(config["docs_dir"]) / "examples" / "_snippets"
        _archive_bytes = _build_zip_bytes(snippets_dir)
    files.append(File.generated(config, _ARCHIVE_URI, content=_archive_bytes))
    return files
