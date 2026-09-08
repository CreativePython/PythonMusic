"""The registry of open files, and the single tabbed window that holds them.

``FileList`` maps filenames <-> EditorWindow instances and owns ``master_window``
(one Toplevel) with its ``ttk.Notebook``: every editor tab lives in that notebook.
``PyShellFileList`` (in pyshell.py) extends it to also manage the Console.
"""

import os
from tkinter import messagebox, Toplevel, Frame, Canvas
from tkinter import ttk

from pem.editing.menubar import window_menus

class FileList:
    "Tracks open editor windows and owns the single tabbed master window."

    # N.B. this import overridden in PyShellFileList.
    from pem.editing.editor import EditorWindow

    def __init__(self, root):
        self.root = root
        self.dict = {}
        self.inversedict = {}
        self.vars = {} # For EditorWindow.getrawvar (shared Tcl variables)

        # --- Tabbed Interface Architecture ---
        # Initialize references for the single master window and its notebook container.
        self.master_window = None
        self.notebook = None

    def _initialize_master_notebook(self):
        """
        Construct the primary IDE window and the Notebook widget if they do not exist.
        This ensures all files open within a single unified interface.
        """
        if self.master_window is None or not self.master_window.winfo_exists():
            # Create the main application window
            self.master_window = Toplevel(self.root)
            self.master_window.title("PEM Editor")
            self.master_window.protocol("WM_DELETE_WINDOW", self.close_all_callback)
            
            # The Window-menu / window-list code calls .wakeup() on window
            # objects; give the master window one (de-iconify + raise).
            def _wakeup():
                if self.master_window.state() == 'iconic':
                    self.master_window.deiconify()
                self.master_window.lift()
            self.master_window.wakeup = _wakeup

            # Apply base geometry (can be overridden by restored preferences later)
            self.master_window.geometry("900x600")

            # Construct the Notebook to hold individual file tabs
            self.notebook = ttk.Notebook(self.master_window)
            self.notebook.pack(fill='both', expand=True)

            # The window carries the menu bar every tab in it works from.
            window_menus(self.master_window, self.EditorWindow.menu_specs)

    def set_run_indicator(self, running):
        """Switch the shared Run toolbar button between its idle (play) and
        running (in-progress) glyphs.

        No-op if the toolbar was built without image icons (the Canvas polygon
        fallback) or the master window no longer exists.
        """
        mw = getattr(self, 'master_window', None)
        if mw is None:
            return
        try:
            if not mw.winfo_exists():
                return
        except Exception:
            return
        btn = getattr(mw, 'global_run_button', None)
        icons = getattr(mw, 'global_run_icons', None)
        if not btn or not icons or not icons[0] or not icons[1]:
            return
        icon = icons[1] if running else icons[0]
        try:
            if isinstance(btn, Canvas):
                btn.itemconfig('icon', image=icon)
            else:
                btn.config(image=icon)
        except Exception:
            pass

    def open(self, filename, action=None):
        """
        Evaluate the requested file path. If the file is already open, focus its tab.
        Otherwise, instantiate a new EditorWindow within the master notebook.
        """
        assert filename
        filename = self.canonize(filename)
        
        if os.path.isdir(filename):
            # Prevent attempts to open directories as text files
            messagebox.showerror(
                "File Error",
                f"{filename!r} is a directory.",
                master=self.root)
            return None
            
        key = os.path.normcase(filename)
        
        # Ensure the UI container exists before opening any files
        self._initialize_master_notebook()

        if key in self.dict:
            # The file is already open. Locate its editor and focus the corresponding tab.
            edit = self.dict[key]
            if hasattr(edit, 'main_container'):
                # A ttk.Notebook tab is identified by its child container widget.
                try:
                    self.notebook.select(edit.main_container)
                except Exception:
                    pass 
            return edit

        if action:
            # Execute a custom action rather than creating a standard editor
            return action(filename)
        else:
            # Instantiate the editor. The EditorWindow class will use self.notebook
            edit = self.EditorWindow(self, filename, key)
            if edit.good_load:
                return edit
            else:
                edit._close()
                return None

    def gotofileline(self, filename, lineno=None):
        """Open a file and immediately scroll to a specific line number."""
        edit = self.open(filename)
        if edit is not None and lineno is not None:
            edit.gotoline(lineno)

    def new(self, filename=None):
        """Generate a new, blank tab within the notebook."""
        self._initialize_master_notebook()
        return self.EditorWindow(self, filename)

    def close_all_callback(self, *args, **kwds):
        """Iterate through all open tabs and request closure (triggering save prompts)."""
        for edit in list(self.inversedict):
            reply = edit.close()
            if reply == "cancel":
                break
        return "break"

    def unregister_maybe_terminate(self, edit):
        """
        Remove an editor from the registry. If no files remain open, 
        terminate the master window and the application root.
        """
        try:
            key = self.inversedict[edit]
        except KeyError:
            print("Don't know this EditorWindow object.  (close)")
            return
            
        if key:
            del self.dict[key]
        del self.inversedict[edit]
        
        if not self.inversedict:
            # No tabs remain. Clean up the UI architecture.
            if self.master_window and self.master_window.winfo_exists():
                self.master_window.destroy()
                self.master_window = None
                self.notebook = None
            self.root.quit()

    def filename_changed_edit(self, edit):
        """Update the registry and tab title when a file is saved under a new name."""
        edit.saved_change_hook()
        try:
            key = self.inversedict[edit]
        except KeyError:
            print("Don't know this EditorWindow object.  (rename)")
            return
            
        filename = edit.io.filename
        if not filename:
            if key:
                del self.dict[key]
            self.inversedict[edit] = None
            return
            
        filename = self.canonize(filename)
        newkey = os.path.normcase(filename)
        if newkey == key:
            return
            
        if newkey in self.dict:
            conflict = self.dict[newkey]
            self.inversedict[conflict] = None
            messagebox.showerror(
                "Name Conflict",
                f"You now have multiple edit tabs open for {filename!r}",
                master=self.root)
                
        self.dict[newkey] = edit
        self.inversedict[edit] = newkey
        if key:
            try:
                del self.dict[key]
            except KeyError:
                pass

    def canonize(self, filename):
        """Standardize the file path format across different operating systems."""
        if not os.path.isabs(filename):
            try:
                pwd = os.getcwd()
            except OSError:
                pass
            else:
                filename = os.path.join(pwd, filename)
        return os.path.normpath(filename)


if __name__ == '__main__':
    from unittest import main
    main('pem.pem_test.test_filelist', verbosity=2)