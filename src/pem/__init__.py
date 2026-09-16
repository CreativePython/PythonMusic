"""The pem package implements PEM, the PythonMusic IDE.

PEM is a Python editor and interactive shell -- a hard fork of CPython's
IDLE.  It needs tcl/tk 8.5 or later.  Launch it via ``PEM.py``.

Everything here is private implementation; details are subject to change.
"""
import sys

testing = False  # A test harness may set this True to suppress GUI side effects.


def isFrozen():
    """Return True when PEM is running as the frozen app built by PEM/build.py.

    Returns False when PEM runs on a regular Python installation (pip-installed,
    or from source).  PythonMusic's own modules keep their own check, since they
    also run inside students' programs, where PEM isn't present.
    """
    return bool(getattr(sys, 'frozen', False))