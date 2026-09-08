""" help.py: Open PEM's documentation.

Help => PythonMusic Docs opens the documentation site in the user's browser.
The same page is reached from the Help menu, the F1 key, and -- on macOS --
the system Help menu, which macosx.overrideRootMenu() points here.
"""
import webbrowser

DOCS_URL = "https://pythonmusic.org/"


def show_pemhelp(parent):
    "Open the PythonMusic documentation in a web browser."
    webbrowser.open(DOCS_URL)


if __name__ == '__main__':
    from unittest import main
    main('pem.pem_test.test_help', verbosity=2, exit=False)

    from pem.pem_test.htest import run
    run(show_pemhelp)
