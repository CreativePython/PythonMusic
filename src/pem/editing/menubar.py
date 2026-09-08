"""The menu bar a PEM window carries.

A window's menus belong to the window, not to anything inside it.  The editor
window holds one menu bar for every tab it opens, and each command acts on the
tab that is showing, so switching tabs leaves the menu bar alone.

``WindowMenus`` builds and owns that menu bar.  ``FileList`` creates one as it
creates the editor window; a window that stands on its own -- the Console --
creates one for itself.  Either way the result lives on the window as
``top.menus``, and each ``EditorWindow`` in it reads its menus from there.

The menu bar is filled with its cascades and their items, then attached to
the window.
"""
import os
import re

from tkinter import BooleanVar, Menu, END, TclError

from pem import macosx
from pem import mainmenu
from pem import window
from pem.config import pemConf


def prepstr(s):
    """Split a menu label on its '_' marker: (underline index, clean label)."""
    i = s.find('_')
    if i >= 0:
        s = s[:i] + s[i+1:]
    return i, s


keynames = {
 'bracketleft': '[',
 'bracketright': ']',
 'slash': '/',
}


def get_accelerator(keydefs, eventname):
    """Return the key combination to show beside a menu item, e.g. "Ctrl+R"."""
    keylist = keydefs.get(eventname)
    if (not keylist) or (macosx.isCocoaTk() and eventname in {
                            "<<open-module>>",
                            "<<goto-line>>",
                            "<<change-indentwidth>>"}):
        return ""
    s = keylist[0]
    s = re.sub(r"-[a-z]\b", lambda m: m.group().upper(), s)
    s = re.sub(r"\b\w+\b", lambda m: keynames.get(m.group(), m.group()), s)
    s = re.sub("Key-", "", s)
    s = re.sub("Cancel", "Ctrl-Break", s)
    s = re.sub("Control-", "Ctrl-", s)
    s = re.sub("-", "+", s)
    s = re.sub("><", " ", s)
    s = re.sub("<", "", s)
    s = re.sub(">", "", s)
    return s


def window_menus(top, menu_specs, attach=True):
    """Return the menus for window ``top``, building them the first time.

    menu_specs -- (cascade name, label) pairs naming the cascades this window
        shows, in menu bar order.  See EditorWindow.menu_specs.
    attach -- False for a window that starts hidden, which attaches its own
        menu bar once it is on screen (see PyShell.show).
    """
    menus = getattr(top, 'menus', None)
    if menus is None:
        menus = top.menus = WindowMenus(top, menu_specs, attach=attach)
    return menus


class WindowMenus:
    "One window's menu bar: its cascades, their items, and what they act on."

    # Labelled with the digit or letter that opens each recent file.
    recent_file_keys = "1234567890ABCDEFGHIJK"

    def __init__(self, top, menu_specs, attach=True):
        self.top = top
        self.menu_specs = menu_specs
        self.menubar = Menu(top)
        self.menudict = {}
        for name, label in menu_specs:
            underline, label = prepstr(label)
            # Tk claims the menu bar child named 'help' as the system Help
            # menu and puts a "PEM Help" item at its top.  PEM's Help menu
            # holds only the entries in mainmenu.menudefs, so the widget takes
            # a name of its own and Tk leaves its contents alone.
            widget_name = 'pemhelp' if name == 'help' else name
            self.menudict[name] = menu = Menu(
                self.menubar, name=widget_name, tearoff=0,
                postcommand=lambda cascade=name: self.run_postcommand(cascade))
            self.menubar.add_cascade(label=label, menu=menu,
                                     underline=underline)
        if macosx.isCarbonTk():
            self.menudict['application'] = menu = Menu(self.menubar,
                                                       name='apple', tearoff=0)
            self.menubar.add_cascade(label='PEM', menu=menu)

        self.fill()

        self.recent_files_menu = Menu(self.menubar, tearoff=0)
        if 'file' in self.menudict:
            self.menudict['file'].insert_cascade(2, label='Open Recent',
                                                 underline=5,
                                                 menu=self.recent_files_menu)
        self.base_helpmenu_length = self.menudict['help'].index(END)
        self.reset_help_menu_entries()
        self.start_window_list()

        if attach:
            top.config(menu=self.menubar)

    # --- what the menus act on -------------------------------------------

    def active_editor(self):
        """The editor a menu command applies to: the tab currently showing."""
        return getattr(self.top, 'current_editor', None)

    def send_event(self, eventname):
        "Fire a virtual event on the active editor, as choosing a menu item does."
        editor = self.active_editor()
        text = getattr(editor, 'text', None)
        try:
            if text is not None and text.winfo_exists():
                text.event_generate(eventname)
        except TclError:
            pass

    def run_postcommand(self, cascade):
        """Let the active editor refresh a cascade as it opens.

        A window that defines ``<cascade>_menu_postcommand`` gets it called
        here; the rest open unchanged.
        """
        editor = self.active_editor()
        refresh = getattr(editor, f'{cascade}_menu_postcommand', None)
        if refresh is not None:
            refresh()

    def get_var_obj(self, eventname, vartype=None):
        "Shared Tcl variable behind a checkbutton menu item."
        editor = self.active_editor()
        if editor is None:
            return None
        return editor.get_var_obj(eventname, vartype)

    # --- building and refreshing ------------------------------------------

    def fill(self, menudefs=None, keydefs=None):
        "Add every cascade's items, with their shortcut labels."
        if menudefs is None:
            menudefs = mainmenu.menudefs
        if keydefs is None:
            keydefs = mainmenu.default_keydefs
        for cascade, entrylist in menudefs:
            menu = self.menudict.get(cascade)
            if not menu:
                continue
            for entry in entrylist:
                if entry is None:
                    menu.add_separator()
                    continue
                label, eventname = entry
                checkbutton = (label[:1] == '!')
                if checkbutton:
                    label = label[1:]
                underline, label = prepstr(label)
                accelerator = get_accelerator(keydefs, eventname)
                command = lambda event=eventname: self.send_event(event)
                if checkbutton:
                    # The variable arrives with the first tab; until then the
                    # item still works, it just starts unticked.
                    variable = self.get_var_obj(eventname, BooleanVar)
                    options = {'variable': variable} if variable else {}
                    menu.add_checkbutton(label=label, underline=underline,
                                         command=command,
                                         accelerator=accelerator, **options)
                else:
                    menu.add_command(label=label, underline=underline,
                                     command=command,
                                     accelerator=accelerator)

    def apply_keybindings(self, keydefs):
        "Relabel every menu item with its shortcut from the given key set."
        events = {}
        for cascade, entrylist in mainmenu.menudefs:
            events[cascade] = {prepstr(item[0])[1]: item[1]
                               for item in entrylist if item}
        for cascade, menu in self.menudict.items():
            end = menu.index(END)
            if end is None:
                continue
            for index in range(0, end + 1):
                if menu.type(index) != 'command':
                    continue
                if not menu.entrycget(index, 'accelerator'):
                    continue
                eventname = events.get(cascade, {}).get(
                    menu.entrycget(index, 'label'))
                if eventname:
                    menu.entryconfig(
                        index, accelerator=get_accelerator(keydefs, eventname))

    def reset_help_menu_entries(self):
        "Rebuild the extra documentation links below PEM's own Help entries."
        helpmenu = self.menudict['help']
        helpmenu_length = helpmenu.index(END)
        if helpmenu_length > self.base_helpmenu_length:
            helpmenu.delete(self.base_helpmenu_length + 1, helpmenu_length)
        help_list = pemConf.GetAllExtraHelpSourcesList()
        if help_list:
            helpmenu.add_separator()
            for name, resource in (entry[:2] for entry in help_list):
                helpmenu.add_command(
                    label=name,
                    command=lambda source=resource: self.open_help_source(source))

    def open_help_source(self, resource):
        "Open one of the extra Help entries: a web page or a local file."
        editor = self.active_editor()
        if editor is not None:
            editor.open_help_source(resource)

    def fill_recent_files(self, file_names):
        "Rebuild the File > Open Recent submenu from the paths given."
        menu = self.recent_files_menu
        menu.delete(0, END)
        for key, file_name in zip(self.recent_file_keys, file_names):
            menu.add_command(
                label=f"{key} {file_name}", underline=0,
                command=lambda path=file_name: self.open_recent_file(path))

    def open_recent_file(self, file_name):
        "Open a file chosen from Open Recent, in the tab that is showing."
        editor = self.active_editor()
        if editor is not None:
            editor.io.open(editFile=file_name)

    # --- the Window menu's list of open windows ---------------------------

    def start_window_list(self):
        """Keep the Window menu's list of open windows up to date.

        The entries above the list are fixed, so they are counted once here;
        everything after them is rebuilt whenever a window opens or closes.
        """
        menu = self.menudict.get('window')
        if menu is None:
            return
        end = menu.index(END)
        self.fixed_window_entries = -1 if end is None else end
        if end is not None:
            menu.add_separator()
            self.fixed_window_entries += 1
        window.register_callback(self.refresh_window_list)
        self.top.bind('<Destroy>', self.stop_window_list, add='+')

    def refresh_window_list(self):
        "Relist the open windows below the Window menu's fixed entries."
        menu = self.menudict['window']
        end = menu.index(END)
        if end is not None and end > self.fixed_window_entries:
            menu.delete(self.fixed_window_entries + 1, end)
        window.add_windows_to_menu(menu)

    def stop_window_list(self, event=None):
        "Stop relisting once the window these menus belong to is gone."
        if event is None or event.widget is self.top:
            window.unregister_callback(self.refresh_window_list)
