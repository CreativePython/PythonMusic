"""Env-var-gated latency log for diagnosing PEM startup / Run delays.

Enable it by setting the ``PEM_PERF`` environment variable before launching
PEM:

    PEM_PERF=1 python PEM.py                       # run from source
    PEM_PERF=1 ./dist/PEM.app/Contents/MacOS/PEM  # run a built .app

When enabled, every ``mark(label)`` call writes a line to:
  * stderr, if a real stderr stream is attached (handy when launched from a
    terminal); a windowed .app launched from Finder usually has none, so also
  * a log file -- ``~/pem_perf.log`` by default, or the path you give as the
    value of ``PEM_PERF`` (anything containing a path separator is treated as
    a path).

The execution subprocess inherits ``PEM_PERF`` (and the GUI and subprocess
share ``~``), so GUI and subprocess marks land in the *same* file, each tagged
with its PID.  Each process measures elapsed time from the moment it first
imported this module, so deltas are *within* a process: to pin down the
"Run pressed -> first output" gap, subtract two marks logged by the same (GUI)
PID; the subprocess marks (a different PID) break down where the child spent its
time.

    from pem import perflog
    perflog.mark("run pressed")
"""
import os
import sys
import time

from pem import isFrozen

_value = os.environ.get("PEM_PERF") or ""
ENABLED = bool(_value)

if os.sep in _value or (os.altsep and os.altsep in _value):
    _logpath = os.path.abspath(os.path.expanduser(_value))
else:
    _logpath = os.path.expanduser("~/pem_perf.log")

_start = time.perf_counter()


def _emit(text):
    # stderr (best effort -- may be None in a windowed app)
    stream = sys.__stderr__ or sys.stderr
    if stream is not None:
        try:
            stream.write(text + "\n")
            stream.flush()
        except Exception:
            pass
    # log file (the reliable channel; append so GUI + subprocess share it)
    try:
        with open(_logpath, "a", encoding="utf-8") as fh:
            fh.write(text + "\n")
    except Exception:
        pass


if ENABLED:
    _emit(f"[perf ======== process start  pid={os.getpid():>6}  frozen={isFrozen()}  "
          f"argv={sys.argv!r}  ========]")


def mark(label):
    """Log ``label`` with elapsed-ms-since-import and PID, if PEM_PERF is set."""
    if not ENABLED:
        return
    elapsed_ms = (time.perf_counter() - _start) * 1000.0
    _emit(f"[perf +{elapsed_ms:10.1f}ms pid={os.getpid():>6}] {label}")
