"""Define the menu bar: cascades, their items, and the virtual events they fire.

``menudefs`` is a list of ``(cascade_name, [(label, '<<event>>') or None, ...])``
where ``None`` is a separator and ``_`` in a label marks its underline key.
EditorWindow (and subclasses) build their real menus from this against each
window's own ``menu_specs``; a window that doesn't declare a given cascade
silently skips it -- so, e.g., the ``shell`` cascade only appears on the shell
window.  ``default_keydefs`` pairs the same virtual events with key bindings.
"""
from importlib.util import find_spec

from pem.config import pemConf

#   Warning: menudefs is altered in macosx.overrideRootMenu()
#   after it is determined that an OS X Aqua Tk is in use,
#   which cannot be done until after Tk() is first called.
#   Do not alter the 'file', 'options', or 'help' cascades here
#   without altering overrideRootMenu() as well.
#       TODO: Make this more robust

menudefs = [
 # underscore prefixes character to underscore
 ('file', [
   ('_New', '<<open-new-window>>'),
   ('_Open...', '<<open-window-from-file>>'),
   ('_Save', '<<save-window>>'),
   ('Save _As...', '<<save-window-as-file>>'),
   ('Save _All', '<<save-all-windows>>'),
   ('Create _Executable', '<<create-executable>>'),
   None,
   ('_Close', '<<close-window>>'),
   ('Close _All', '<<close-all-windows>>'),
   None,
   ('_Print...', '<<print-window>>'),
   None,
   ('_Preferences...', '<<open-config-dialog>>'),
   None,
   ('_Quit', '<<quit>>'),
   ]),

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
   ('_Toggle Comments', '<<toggle-comment>>'),
   ]),

#  ('format', [
#    ('F_ormat Paragraph', '<<format-paragraph>>'),
#    ('_Indent Region', '<<indent-region>>'),
#    ('_Dedent Region', '<<dedent-region>>'),
#    ('Tabify Region', '<<tabify-region>>'),
#    ('Untabify Region', '<<untabify-region>>'),
#    ('Toggle Tabs', '<<toggle-tabs>>'),
#    ('New Indent Width', '<<change-indentwidth>>'),
#    ('S_trip Trailing Whitespace', '<<do-rstrip>>'),
#    ]),

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

#  ('options', [
#    ('Configure _PEM', '<<open-config-dialog>>'),
#    None,
#    ('Show _Code Context', '<<toggle-code-context>>'),
#    ('Show _Line Numbers', '<<toggle-line-numbers>>'),
#    ('_Zoom Height', '<<zoom-height>>'),
#    ]),

 ('window', [
   ]),

 ('help', [
   ('_JythonMusic Docs', '<<jythonmusic-docs>>'),
   ('_Python Docs', '<<python-docs>>'),
   None,
   ('_About PEM...', '<<about-pem>>'),
   ]),
]

# if find_spec('turtledemo'):
#     menudefs[-1][1].append(('Turtle Demo', '<<open-turtle-demo>>'))

default_keydefs = pemConf.GetCurrentKeySet()

if __name__ == '__main__':
    from unittest import main
    main('pem.pem_test.test_mainmenu', verbosity=2)
