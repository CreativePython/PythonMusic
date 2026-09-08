"""Define the menu bar: cascades, their items, and the virtual events they fire.

``menudefs`` is a list of ``(cascade_name, [(label, '<<event>>') or None, ...])``
where ``None`` is a separator and ``_`` in a label marks its underline key.
EditorWindow (and subclasses) build their real menus from this against each
window's own ``menu_specs``; a window that doesn't declare a given cascade
silently skips it -- so, e.g., the ``run`` cascade appears on the editor window
but not on the Console.  ``default_keydefs`` pairs the same virtual events with
key bindings.

``build_menudefs()`` returns the finished menu set for one platform, and
``pem.macosx.setupApp()`` rebuilds ``menudefs`` with ``mac_app_menu=True``
before any window builds its menu bar, so every window reads the same list.
"""
from pem.config import pemConf


def build_menudefs(mac_app_menu=False, carbon_app_cascade=False):
    """Return the menu definitions for one platform.

    mac_app_menu -- True on macOS, where the system's application menu provides
    Preferences and Quit, so the File cascade leaves them out.  About PEM stays
    in the Help menu on every platform: the menus should match across operating
    systems, even though macOS also offers About in its application menu.

    carbon_app_cascade -- True on Carbon Aqua Tk, which needs an 'application'
    cascade of PEM's own to hold About PEM.  Cocoa Aqua Tk fills that menu
    itself, from the Tcl commands macosx.overrideRootMenu() registers.
    """
    file_items = [
        ('_New', '<<open-new-window>>'),
        ('_Open...', '<<open-window-from-file>>'),
        ('_Save', '<<save-window>>'),
        ('Save _As...', '<<save-window-as-file>>'),
        ('Save _All', '<<save-all-windows>>'),
        # ('Create _Executable', '<<create-executable>>'),
        None,
        ('_Close', '<<close-window>>'),
        ('Close _All', '<<close-all-windows>>'),
        None,
        ('_Print...', '<<print-window>>'),
        ]
    if not mac_app_menu:
        file_items += [
            None,
            ('_Preferences...', '<<open-config-dialog>>'),
            None,
            ('_Quit', '<<quit>>'),
            ]

    help_items = [
        ('_PythonMusic Docs', '<<pythonmusic-docs>>'),
        ('_About PEM...', '<<about-pem>>'),
        ]

    cascades = []
    if carbon_app_cascade:
        cascades.append(
     ('application', [
       ('About PEM...', '<<about-pem>>'),
       None,
       ]))

    return cascades + [
     ('file', file_items),

     ('edit', [
       ('_Undo', '<<undo>>'),
       ('_Redo', '<<redo>>'),
       None,
       ('Cu_t', '<<cut>>'),
       ('_Copy', '<<copy>>'),
       ('_Paste', '<<paste>>'),
       ('Select _All', '<<select-all>>'),
       None,
       ('_Find...', '<<find>>'),
       ('R_eplace...', '<<replace>>'),
       None,
       ('_Indent Region', '<<indent-region>>'),
       ('_Dedent Region', '<<dedent-region>>'),
       None,
       ('_Toggle Comment', '<<toggle-comment>>'),
       ]),

     ('run', [
       ('_Run', '<<run-module>>'),
       ('Run _Selection', '<<run-selection>>'),
       ('Run Current _Line', '<<run-current-line>>'),
       ('Run Current _Paragraph', '<<run-current-paragraph>>'),
      #  ('_Pause', '<<pause>>'),   # disabled - functionality not yet implemented
       ('_Stop', '<<stop-script>>'),
       None,
       ('Show _Console', '<<open-python-shell>>'),
       ]),

     ('shell', [
       ('_View Last Restart', '<<view-restart>>'),
       ('_Restart Console', '<<restart-shell>>'),
       None,
       ('_Previous History', '<<history-previous>>'),
       ('_Next History', '<<history-next>>'),
       None,
       ('_Interrupt Execution', '<<interrupt-execution>>'),
       ]),

     ('window', [
       ]),

     ('help', help_items),
    ]


menudefs = build_menudefs()

default_keydefs = pemConf.GetCurrentKeySet()

if __name__ == '__main__':
    from unittest import main
    main('pem.pem_test.test_mainmenu', verbosity=2)
