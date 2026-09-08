"""PyInstaller entry point for the frozen PEM build.

This wrapper exists only for the frozen application.  It performs the
bundle-specific bootstrap (locate the extracted runtime, put the bundled
``pem`` package and standard library on ``sys.path``), routes the execution
subprocess that a frozen build re-launches via ``--pem-subprocess``, handles
PyInstaller's internal dependency-check invocation, and then hands off to the
normal editor entry in ``pem.__main__``.

The pip-installed ``pem`` command does NOT use this file; it calls
``pem.__main__:main`` directly.
"""

import sys
import os
import multiprocessing
from pathlib import Path

LIB_FOLDER_NAME = "pem"
SUBPROCESS_FLAG = "--pem-subprocess"  # must match interpreter.SUBPROCESS_FLAG


def getBundlePath():
    """Root of the extracted PyInstaller bundle (this file's dir when unfrozen)."""
    if getattr(sys, 'frozen', False):
        return Path(getattr(sys, '_MEIPASS', Path(sys.executable).parent))
    return Path(__file__).parent


def configureSystemPaths():
    """Put the bundled ``pem`` package and standard library on sys.path."""
    rootPath = getBundlePath()

    libraryPath = rootPath / LIB_FOLDER_NAME
    if str(libraryPath) not in sys.path:
        sys.path.insert(0, str(libraryPath))

    standardLibPath = rootPath / "python_lib"
    if standardLibPath.exists() and str(standardLibPath) not in sys.path:
        sys.path.append(str(standardLibPath))


# Initialize bundle paths immediately upon import
configureSystemPaths()


def runSubprocessServer(port):
    """Run the RPC server that executes user code (the --pem-subprocess role)."""
    try:
        rootPath = getBundlePath()
        if str(rootPath) not in sys.path:
            sys.path.insert(0, str(rootPath))

        # Re-route sys.argv to satisfy the expectations of the interpreter module
        sys.argv = ["pem_subprocess", str(port)]

        from pem.interpreter.run import main
        main()

    except Exception as error:
        print(f"PEM Subprocess Error: {error}", file=sys.stderr)
        sys.exit(1)


def main():
    """Frozen-build entry: handle the bundle-only cases, else launch the editor."""
    # Necessary for PyInstaller to manage multiprocessing correctly
    multiprocessing.freeze_support()

    # Internal subprocess request (a frozen build re-launches itself this way)
    if len(sys.argv) >= 3 and sys.argv[1] == SUBPROCESS_FLAG:
        runSubprocessServer(int(sys.argv[2]))
        return

    # PyInstaller dependency check (internal use)
    if len(sys.argv) >= 2 and "_child.py" in sys.argv[1]:
        import runpy
        targetFile = sys.argv[1]
        sys.argv = sys.argv[1:]
        runpy.run_path(targetFile, run_name='__main__')
        return

    # Normal launch (including file drag-and-drop) -> shared editor entry
    from pem.__main__ import main as launchEditorEntry
    launchEditorEntry()


if __name__ == "__main__":
    main()
