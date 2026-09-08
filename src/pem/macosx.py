"""
A number of functions that enhance PEM on macOS.
"""
from os.path import expanduser
import plistlib
from sys import platform  # Used in _init_tk_type, changed by test.

import tkinter


## Define functions that query the Mac graphics type.
## _tk_type and its initializer are private to this section.

_tk_type = None

def _init_tk_type():
    """ Initialize _tk_type for isXyzTk functions.

    This function is only called once, when _tk_type is still None.
    """
    global _tk_type
    if platform == 'darwin':

        # When running PEM, GUI is present, test/* may not be.
        # When running tests, test/* is present, GUI may not be.
        # If not, guess most common.  Does not matter for testing.
        from pem.__init__ import testing
        if testing:
            from test.support import requires, ResourceDenied
            try:
                requires('gui')
            except ResourceDenied:
                _tk_type = "cocoa"
                return

        root = tkinter.Tk()
        ws = root.tk.call('tk', 'windowingsystem')
        if 'x11' in ws:
            _tk_type = "xquartz"
        elif 'aqua' not in ws:
            _tk_type = "other"
        elif 'AppKit' in root.tk.call('winfo', 'server', '.'):
            _tk_type = "cocoa"
        else:
            _tk_type = "carbon"
        root.destroy()
    else:
        _tk_type = "other"
    return

def isAquaTk():
    """
    Returns True if PEM is using a native OS X Tk (Cocoa or Carbon).
    """
    if not _tk_type:
        _init_tk_type()
    return _tk_type == "cocoa" or _tk_type == "carbon"

def isCarbonTk():
    """
    Returns True if PEM is using a Carbon Aqua Tk (instead of the
    newer Cocoa Aqua Tk).
    """
    if not _tk_type:
        _init_tk_type()
    return _tk_type == "carbon"

def isCocoaTk():
    """
    Returns True if PEM is using a Cocoa Aqua Tk.
    """
    if not _tk_type:
        _init_tk_type()
    return _tk_type == "cocoa"

def isXQuartz():
    """
    Returns True if PEM is using an OS X X11 Tk.
    """
    if not _tk_type:
        _init_tk_type()
    return _tk_type == "xquartz"


def readSystemPreferences():
    """
    Fetch the macOS system preferences.
    """
    if platform != 'darwin':
        return None

    plist_path = expanduser('~/Library/Preferences/.GlobalPreferences.plist')
    try:
        with open(plist_path, 'rb') as plist_file:
            return plistlib.load(plist_file)
    except OSError:
        return None


def preferTabsPreferenceWarning():
    """
    Warn if "Prefer tabs when opening documents" is set to "Always".
    """
    if platform != 'darwin':
        return None

    prefs = readSystemPreferences()
    if prefs and prefs.get('AppleWindowTabbingMode') == 'always':
        return (
            'WARNING: The system preference "Prefer tabs when opening'
            ' documents" is set to "Always". This will cause various problems'
            ' with PEM. For the best experience, change this setting when'
            ' running PEM (via System Preferences -> Dock).'
        )
    return None


def isDarkMode():
    """
    Returns True if macOS is in dark mode, False otherwise.
    Returns None on non-macOS systems.
    """
    if platform != 'darwin':
        return None

    prefs = readSystemPreferences()
    if prefs:
        # Check for dark mode appearance setting
        appearance = prefs.get('AppleInterfaceStyle')
        return appearance == 'Dark'
    return False


## Fix the menu and related functions.

def addOpenEventSupport(root, flist):
    """
    This ensures that the application will respond to open AppleEvents, which
    makes is feasible to use PEM as the default application for python files.
    """
    def doOpenFile(*args):
        for fn in args:
            flist.open(fn)

    # The command below is a hook in aquatk that is called whenever the app
    # receives a file open event. The callback can have multiple arguments,
    # one for every file that should be opened.
    root.createcommand("::tk::mac::OpenDocument", doOpenFile)

def hideTkConsole(root):
    try:
        root.tk.call('console', 'hide')
    except tkinter.TclError:
        # Some versions of the Tk framework don't have a console object
        pass

def overrideRootMenu(root, flist):
    """
    Replace the Tk root menu by something that is more appropriate for
    PEM with an Aqua Tk.
    """
    # The menu that is attached to the Tk root (".") is also used by AquaTk for
    # all windows that don't specify a menu of their own. The default menubar
    # contains a number of menus, none of which are appropriate for PEM. The
    # Most annoying of those is an 'About Tck/Tk...' menu in the application
    # menu.
    #
    # This function replaces the default menubar by a mostly empty one, it
    # should only contain the correct application menu and the window menu.
    #
    # Due to a (mis-)feature of TkAqua the user will also see an empty Help
    # menu.
    from tkinter import Menu
    from pem import mainmenu
    from pem import window

    # Build the menu set that suits macOS: Preferences, Quit and About PEM
    # come from the application menu, so the File and Help cascades leave them
    # out.  Carbon Tk needs its own 'application' cascade to hold About.
    # This runs before any window builds its menu bar.
    mainmenu.menudefs = mainmenu.build_menudefs(mac_app_menu=True,
                                                carbon_app_cascade=isCarbonTk())

    menubar = Menu(root)
    root.configure(menu=menubar)

    menu = Menu(menubar, name='window', tearoff=0)
    menubar.add_cascade(label='Window', menu=menu, underline=0)

    def postwindowsmenu(menu=menu):
        end = menu.index('end')
        if end is None:
            end = -1

        if end > 0:
            menu.delete(0, end)
        window.add_windows_to_menu(menu)
    window.register_callback(postwindowsmenu)

    def about_dialog(event=None):
        "Handle Help 'About PEM' event."
        # Synchronize with editor.EditorWindow.about_dialog.
        from pem import about
        about.AboutDialog(root)

    def config_dialog(event=None):
        "Handle Options 'Configure PEM' event."
        # Synchronize with editor.EditorWindow.config_dialog.
        from pem.config import configdialog

        # Ensure that the root object has an instance_dict attribute,
        # mirrors code in EditorWindow (although that sets the attribute
        # on an EditorWindow instance that is then passed as the first
        # argument to ConfigDialog)
        root.instance_dict = flist.inversedict
        configdialog.ConfigDialog(root, 'Settings')

    def help_dialog(event=None):
        "Handle Help 'PEM Help' event."
        # Synchronize with editor.EditorWindow.help_dialog.
        from pem.dialogs import help
        help.show_pemhelp(root)

    root.bind('<<about-pem>>', about_dialog)
    root.bind('<<open-config-dialog>>', config_dialog)
    root.createcommand('::tk::mac::ShowPreferences', config_dialog)
    if flist:
        root.bind('<<close-all-windows>>', flist.close_all_callback)

        # The binding above doesn't reliably work on all versions of Tk
        # on macOS. Adding command definition below does seem to do the
        # right thing for now.
        root.createcommand('::tk::mac::Quit', flist.close_all_callback)

    if isCarbonTk():
        # for Carbon AquaTk, replace the default Tk apple menu
        menu = Menu(menubar, name='apple', tearoff=0)
        menubar.add_cascade(label='PEM', menu=menu)
    if isCocoaTk():
        # replace default About dialog with About PEM one
        root.createcommand('tkAboutDialog', about_dialog)
        # replace default "Help" item in Help menu
        root.createcommand('::tk::mac::ShowHelp', help_dialog)

def fixb2context(root):
    '''Removed bad AquaTk Button-2 (right) and Paste bindings.

    They prevent context menu access and seem to be gone in AquaTk8.6.
    See issue #24801.
    '''
    root.unbind_class('Text', '<B2>')
    root.unbind_class('Text', '<B2-Motion>')
    root.unbind_class('Text', '<<PasteSelection>>')

def hideSystemEditMenuItems():
    """Keep macOS's Start Dictation and Emoji & Symbols out of the Edit menu.

    macOS reads a menu bar for an Edit menu as it is attached to a window and
    adds four items of its own to it.  These two settings turn two of them
    off; Writing Tools and AutoFill have no such setting and stay.

    Call this before Tk() -- macOS reads the settings as it builds its
    application object, and a call after that is too late for the Emoji &
    Symbols item.  Safe on any platform: elsewhere there is nothing to read
    them.

    The frozen app carries the same two keys in its Info.plist (see
    PEM/build.py), so a built PEM behaves the same without pyobjc.
    ``registerDefaults_`` supplies them as defaults rather than writing to the
    user's preferences, so anyone who wants those items can turn them back on.
    """
    try:
        from Foundation import NSUserDefaults
    except ImportError:
        return
    NSUserDefaults.standardUserDefaults().registerDefaults_({
        'NSDisabledDictationMenuItem': True,
        'NSDisabledCharacterPaletteMenuItem': True,
    })


def _setDockIcon():
    """Set the macOS Dock icon when running as a plain Python process.

    No-op when running as a bundled .app (PyInstaller sets the icon via the
    .icns file) or when pyobjc-framework-Cocoa is not installed.
    """
    import sys, os
    if getattr(sys, 'frozen', False):
        return
    try:
        from AppKit import NSApp, NSImage
        iconPath = os.path.join(os.path.dirname(__file__), 'icons', 'icon_rounded.png')
        image = NSImage.alloc().initWithContentsOfFile_(iconPath)
        if image is not None:
            NSApp.setApplicationIconImage_(image)
    except ImportError:
        pass


def setApplicationName(name):
    """Show *name* (e.g. 'PEM') in the macOS menu bar and Dock.

    When PEM runs as a plain Python process (such as ``python -m pem``), macOS
    labels it 'Python' -- the name of the executable that is actually running.
    That makes sense to a developer but is confusing for a student. Overriding
    the running bundle's CFBundleName makes the menu bar and Dock show PEM's
    name instead.

    macOS reads the name when it builds the menu bar, so this must be called
    before the first Tk() (which creates the underlying NSApplication).

    No-op when not on macOS, when running as a bundled .app (PyInstaller sets
    the name from the bundle's Info.plist), or when pyobjc-framework-Cocoa is
    not installed.
    """
    import sys
    if platform != 'darwin' or getattr(sys, 'frozen', False):
        return
    try:
        from Foundation import NSBundle, NSProcessInfo
    except ImportError:
        return

    # The menu bar reads CFBundleName; the Dock and Activity Monitor prefer the
    # process name. Set all of them so the name is consistent wherever macOS
    # looks. (The Dock of an unbundled process may still fall back to the
    # executable name -- see the note in the module/caller.)
    bundle = NSBundle.mainBundle()
    if bundle is not None:
        info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
        if info is not None:
            info['CFBundleName'] = name
            info['CFBundleDisplayName'] = name

    try:
        NSProcessInfo.processInfo().setProcessName_(name)
    except (AttributeError, ValueError):
        pass


def setupApp(root, flist):
    """
    Perform initial OS X customizations if needed.
    Called from pyshell.main() after initial calls to Tk()

    There are currently three major versions of Tk in use on OS X:
        1. Aqua Cocoa Tk (native default since OS X 10.6)
        2. Aqua Carbon Tk (original native, 32-bit only, deprecated)
        3. X11 (supported by some third-party distributors, deprecated)
    There are various differences among the three that affect PEM
    behavior, primarily with menus, mouse key events, and accelerators.
    Some one-time customizations are performed here.
    Others are dynamically tested throughout pem by calls to the
    isAquaTk(), isCarbonTk(), isCocoaTk(), isXQuartz() functions which
    are initialized here as well.
    """
    if isAquaTk():
        hideTkConsole(root)
        overrideRootMenu(root, flist)
        addOpenEventSupport(root, flist)
        fixb2context(root)
        _setDockIcon()


if __name__ == '__main__':
    from unittest import main
    main('pem.pem_test.test_macosx', verbosity=2)
