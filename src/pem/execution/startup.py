"""Settings PEM applies inside a fresh execution subprocess.

Student code never runs in the PEM editor's own process: shell input, Run
Module, and every shell restart all run in an execution subprocess
(``pem.execution.run``), which starts as essentially bare Python.  So any
default PEM wants to change for user code has to be changed *there*,
once, before their code gets a chance to run.

This module is the one place those changes live.  ``run.main()`` calls
``apply_startup_settings()`` while the subprocess is still starting up --
before it accepts any RPC request from the editor -- and each function
listed in ``_STARTUP_SETTINGS`` runs, in order, in the child.

To add a setting:

  1. Write a function that takes no arguments and makes the change.  Its
     docstring should say what a user would run into without it.
  2. Add the function to ``_STARTUP_SETTINGS``.

Keep each one self-contained and cheap.  They run during the startup of
*every* subprocess, including the pre-warmed spare PEM keeps in the wings
(see ``pyshell.ModifiedInterpreter``), so slow work here shows up as a
slower Run.  A setting that raises is skipped rather than taking the
subprocess -- and the user's session -- down with it.
"""
import os
import sys
import traceback


def allow_printing_huge_integers():
    """Let user code print integers of any size."""
    sys.set_int_max_str_digits(0)


def default_matplotlib_to_qt():
    """Point matplotlib at the Qt backend unless the user chose another.

    PySide6 ships with PEM and is available in any from-source install, and
    qtagg cooperates with the subprocess's idle-tick event pump (see
    ``run.pump_gui_events``), which is what keeps plot windows painting
    while the shell waits for input.  ``setdefault`` leaves an MPLBACKEND
    set before PEM launched alone.
    """
    os.environ.setdefault("MPLBACKEND", "qtagg")


# Applied in this order, once, as each execution subprocess starts.
_STARTUP_SETTINGS = (
    allow_printing_huge_integers,
    default_matplotlib_to_qt,
)


def apply_startup_settings():
    "Apply every setting in _STARTUP_SETTINGS to this subprocess."
    for apply_setting in _STARTUP_SETTINGS:
        try:
            apply_setting()
        except Exception:
            # A setting that won't apply costs a convenience; it is not a
            # reason to stop the subprocess from running user code.  The
            # report goes to the real stderr -- the terminal PEM was
            # launched from, if there is one -- so it can never appear in
            # the shell window the user is working in.
            if sys.__stderr__ is not None:
                print(f"PEM: startup setting {apply_setting.__name__!r} "
                      f"could not be applied.", file=sys.__stderr__)
                traceback.print_exc(file=sys.__stderr__)
