"""The editor window: the code text widget and everything attached to it.

``EditorWindow`` wires up the text widget, the colorizer/undo/percolator stack,
the menus, status bar, line numbers, code context, search/replace, and the Run
bindings (``ScriptBinding``).  Editor windows live as tabs in ``FileList``'s
single master window, which also carries the shared toolbar; each tab has its
own read-only output pane below the editor (``write_output`` / ``clear_output``).
The Console window (``PyShell``) subclasses this via ``OutputWindow`` and opts
out of the tabbed layout.
"""
import importlib.abc
import importlib.util
import os
import platform
import re
import string
import sys
import tokenize
import traceback
import webbrowser

from tkinter import *
from tkinter.font import Font
from tkinter.ttk import Notebook, PanedWindow
from tkinter import simpledialog
from tkinter import messagebox

from pem.config import pemConf
from pem.config import configdialog
from pem.searching import grep
from pem.dialogs import help
from pem import about
from pem import macosx
from pem.text.multicall import MultiCallCreator
from pem.text import pyparse
from pem.dialogs import query
from pem.searching import replace
from pem.searching import search
from pem.editing.tree import wheel_event
from pem.util import py_extensions
from pem import window
from pem.editing import exebuilder

# The default tab setting for a Text widget, in average-width characters.
TK_TABWIDTH_DEFAULT = 8
_py_version = ' (%s)' % platform.python_version()
darwin = sys.platform == 'darwin'

def _sphinx_version():
    "Format sys.version_info to produce the Sphinx version string used to install the chm docs"
    major, minor, micro, level, serial = sys.version_info
    release = f'{major}{minor}'
    release += f'{micro}'
    if level == 'candidate':
        release += f'rc{serial}'
    elif level != 'final':
        release += f'{level[0]}{serial}'
    return release


class EditorWindow:
    "One code-editor tab: text widget, editing machinery, menus, and output pane."
    from pem.text.percolator import Percolator
    from pem.text.colorizer import ColorDelegator, color_config
    from pem.text.undo import UndoDelegator
    from pem.editing.iomenu import IOBinding, encoding
    from pem import mainmenu
    from pem.editing.statusbar import MultiStatusBar
    from pem.editing.codecontext import CodeContext
    from pem.shell.sidebar import LineNumbers
    from pem.text.format import FormatParagraph, FormatRegion, Indents, Rstrip
    from pem.text.parenmatch import ParenMatch
    from pem.editing.zoomheight import ZoomHeight

    filesystemencoding = sys.getfilesystemencoding()  # for file names
    help_url = None

    allow_code_context = True
    allow_line_numbers = True
    allow_highlight_current_line = True
    user_input_insert_tags = None

    def __init__(self, flist=None, filename=None, key=None, root=None):
        from pem.editing.runscript import ScriptBinding

        if EditorWindow.help_url is None:
            dochome =  os.path.join(sys.base_prefix, 'Doc', 'index.html')
            if sys.platform.count('linux'):
                pyver = 'python-docs-' + '%s.%s.%s' % sys.version_info[:3]
                if os.path.isdir('/var/www/html/python/'):  
                    dochome = '/var/www/html/python/index.html'
                else:
                    basepath = '/usr/share/doc/'  
                    dochome = os.path.join(basepath, pyver,
                                           'Doc', 'index.html')
            elif sys.platform[:3] == 'win':
                import winreg  
                docfile = ''
                KEY = (rf"Software\Python\PythonCore\{sys.winver}"
                        r"\Help\Main Python Documentation")
                try:
                    docfile = winreg.QueryValue(winreg.HKEY_CURRENT_USER, KEY)
                except FileNotFoundError:
                    try:
                        docfile = winreg.QueryValue(winreg.HKEY_LOCAL_MACHINE,
                                                    KEY)
                    except FileNotFoundError:
                        pass
                if os.path.isfile(docfile):
                    dochome = docfile
            elif sys.platform == 'darwin':
                dochome = os.path.join(sys.base_prefix,
                        'Resources/English.lproj/Documentation/index.html')
            dochome = os.path.normpath(dochome)
            if os.path.isfile(dochome):
                EditorWindow.help_url = dochome
                if sys.platform == 'darwin':
                    EditorWindow.help_url = 'file://' + EditorWindow.help_url
            else:
                EditorWindow.help_url = ("https://docs.python.org/%d.%d/"
                                         % sys.version_info[:2])
        self.flist = flist
        root = root or flist.root
        self.root = root

        # ---------------------------------------------------------------------
        # SUBSYSTEM: HYBRID TABBED ARCHITECTURE
        # Pedagogical Design: Code editors launch as cohesive tabs within a single
        # Master Notebook. The Interactive Console breaks out into a standalone 
        # OS window to serve as a pure REPL.
        # ---------------------------------------------------------------------

        # Detect window type safely using local import to avoid circular dependencies
        try:
            from pem.shell import outwin
            self.is_shell = isinstance(self, outwin.OutputWindow)
        except Exception:
            self.is_shell = self.__class__.__name__ in ('PyShell', 'OutputWindow')

        if flist and hasattr(flist, 'notebook') and flist.notebook and not getattr(self, 'is_shell', False):
            # Mount window to the Notebook interface
            self.top = top = flist.master_window
            
            # -----------------------------------------------------------------
            # SUBSYSTEM: TAB STYLING ENGINE
            # -----------------------------------------------------------------
            from tkinter.ttk import Style
            style = Style(top)
            
            # Use native everywhere except Linux... macOS gets Aqua, Windows gets vista, Linux gets clam. 
            # This gives you native-looking tabs on the two platforms with the best native themes, 
            # and clam on Linux where it's the better choice.
            if sys.platform.startswith('linux') and 'clam' in style.theme_names():
                style.theme_use('clam')


            # Force Left-Justification for the tabs themselves, but anchor the text East (Right)
            style.configure('TNotebook', tabposition='nw')

            # Override the default Notebook layout so the tab bar doesn't
            # get centered on Aqua. The default layout wraps the client
            # in a centering element on some themes; using a flat
            # client-only layout lets tabposition='nw' take effect.
            style.layout('TNotebook', [('Notebook.client', {'sticky': 'nswe'})])

            style.configure('TNotebook.Tab',
                            padding=[16, 4, 16, 4],
                            anchor='e',
                            background='#e0e0e0',
                            lightcolor='#e0e0e0',
                            borderwidth=1)

            style.map('TNotebook.Tab',
                      background=[('selected', '#ffffff'), ('active', '#f4f4f4')],
                      foreground=[('selected', '#000000'), ('!selected', '#555555')],
                      expand=[('selected', [1, 1, 1, 0])])


            # -----------------------------------------------------------------
            # SUBSYSTEM: TAB TITLE GENERATOR
            # -----------------------------------------------------------------
            # Track the number of untitled workspaces globally across the session 
            # to prevent identically named tabs and preserve UX clarity.
            if not hasattr(flist, 'untitled_count'):
                flist.untitled_count = 0
            flist.untitled_count += 1
            
            # Save the numbered name to the editor instance so it survives updates
            self.untitled_name = f"untitled {flist.untitled_count}"
            initial_tab_title = f"{self.untitled_name}   ✕"

            self.main_container = Frame(flist.notebook)
            flist.notebook.add(self.main_container, text=initial_tab_title)
            flist.notebook.select(self.main_container)

            self.menubar = Menu(top)
            top.config(menu=self.menubar)
            
            # --- TAB FOCUS LOGIC ---
            def on_tab_change(event):
                try:
                    if self.text and self.text.winfo_exists():
                        if flist.notebook.select() == str(self.main_container):
                            top.current_editor = self  
                            top.config(menu=self.menubar)
                            self.text.focus_set()
                            self.text.update_idletasks()
                except Exception:
                    pass
            flist.notebook.bind('<<NotebookTabChanged>>', on_tab_change, add='+')

            # --- TAB CLOSE BUTTON HITBOX LOGIC ---
            def on_notebook_click(event):
                """
                Intercepts clicks on the notebook. Clicks in a fixed-width zone
                at the tab's right edge close the tab; clicks anywhere else fall
                through to ttk's normal tab-selection handling.
                """

                # NOTES:  
                # 
                #  *  Clicking anywhere on the tab title (including its last letter, regardless of length) 
                #     selects that tab. Focus goes to the editor text via existing <<NotebookTabChanged>> handler.
                #
                #  *  Clicking on the ✕ — or within ~14 px of it on either side — closes the tab.
                #
                #  *  Clicking in dead space outside any tab does nothing.


                # hardwired hit area... (also see below)
                CLOSE_HITBOX_PX = 28      # ✕ glyph + small comfort margin

                # adaptive hit area... (uncomment to use)
                #
                # NOTE:  Use this instead, if you want it adaptive — i.e., compute actual rendered width 
                #        of the close glyph from tab's font.
                #
                # import tkinter.font as tkfont
                
                # style = ttk.Style()
                # _tab_font = tkfont.nametofont(style.lookup('TNotebook.Tab', 'font') or 'TkDefaultFont')
                # CLOSE_HITBOX_PX = _tab_font.measure(" ✕") + 10   # glyph + leading space + comfort margin

                try:
                    if 'Notebook' not in event.widget.winfo_class():
                        return

                    try:
                        tabIndex = flist.notebook.index(f"@{event.x},{event.y}")
                    except TclError:
                        return    # Click missed every tab.

                    # Confirm the click landed on an actual tab element (not on an
                    # empty area to the right that index() snapped to the nearest tab).
                    if 'tab' not in flist.notebook.identify(event.x, event.y) and \
                       'label' not in flist.notebook.identify(event.x, event.y):
                        return

                    # Probe CLOSE_HITBOX_PX to the right of the click. If that probe
                    # lands on a different tab (or off the tabs entirely), the click
                    # was within the close zone at the tab's right edge.
                    probe_x = event.x + CLOSE_HITBOX_PX
                    try:
                        probeIndex = flist.notebook.index(f"@{probe_x},{event.y}")
                        in_close_zone = (probeIndex != tabIndex)
                    except TclError:
                        in_close_zone = True    # Probe ran off the end of the tabs.

                    if not in_close_zone:
                        return    # Let ttk handle tab selection normally.

                    # Find the matching editor and close it.
                    clickedTabWidget = flist.notebook.tabs()[tabIndex]
                    for editor in list(top.instance_dict.keys()):
                        if (hasattr(editor, 'main_container') and
                            str(editor.main_container) == clickedTabWidget):

                            def safe_close(targetEditor=editor):
                                # Defer to close(), which closes this tab or --
                                # if it is the last one -- exits PEM.
                                targetEditor.close()

                            editor.text.after(10, safe_close)
                            return "break"
                except Exception:
                    pass



            # Ensure we only bind this click listener to the Master Notebook once
            if not getattr(flist.notebook, 'close_hitbox_bound', False):
                flist.notebook.bind('<Button-1>', on_notebook_click, add='+')
                flist.notebook.close_hitbox_bound = True


            # --- TAB DRAG-TO-REORDER ---
            # Press records which tab the user grabbed. Motion swaps it
            # with whatever tab the cursor is over. Release clears state.
            # Bound only once per notebook (like the close hitbox).
            if not getattr(flist.notebook, 'reorder_bound', False):

                def _on_tab_press(event):
                    nb = event.widget
                    if 'Notebook' not in nb.winfo_class():
                        return
                    try:
                        idx = nb.index(f"@{event.x},{event.y}")
                    except TclError:
                        nb._drag_tab = None
                        return
                    # Only start a drag if the press is actually on a tab.
                    elem = nb.identify(event.x, event.y)
                    if 'tab' not in elem and 'label' not in elem:
                        nb._drag_tab = None
                        return
                    nb._drag_tab = idx
                    nb._drag_started = False   # set True on first motion

                def _on_tab_drag(event):
                    nb = event.widget
                    src = getattr(nb, '_drag_tab', None)
                    if src is None:
                        return

                    # On first motion, mark the dragged tab visually so the
                    # gesture is visible before the cursor crosses a neighbor.
                    if not getattr(nb, '_drag_started', False):
                        nb._drag_started = True
                        try:
                            # Hand/grab cursor signals "drag in progress."
                            nb.configure(cursor='fleur')
                        except TclError:
                            pass

                    try:
                        dst = nb.index(f"@{event.x},{event.y}")
                    except TclError:
                        return
                    if dst == src:
                        return

                    try:
                        nb.insert(dst, nb.tabs()[src])
                        nb._drag_tab = dst
                    except TclError:
                        pass

                def _on_tab_release(event):
                    nb = event.widget
                    nb._drag_tab = None
                    nb._drag_started = False
                    try:
                        nb.configure(cursor='')   # restore default cursor
                    except TclError:
                        pass

                flist.notebook.bind('<ButtonPress-1>', _on_tab_press, add='+')
                flist.notebook.bind('<B1-Motion>',     _on_tab_drag,  add='+')
                flist.notebook.bind('<ButtonRelease-1>', _on_tab_release, add='+')
                flist.notebook.reorder_bound = True


        else:
            # Mount window as a standalone legacy Toplevel
            self.menubar = Menu(root)
            if getattr(self, 'is_shell', False):
                # Don't associate the menubar with the Toplevel while it's hidden —
                # doing so leaks the shell's menu into the editor's window on some
                # platforms. _show_and_focus() attaches the menu when the shell
                # is actually displayed.
                self.top = top = window.ListedToplevel(root)
                top.withdraw()
            else:
                self.top = top = window.ListedToplevel(root, menu=self.menubar)

            self.main_container = top


        if flist:
            self.tkinter_vars = flist.vars
            self.top.instance_dict = flist.inversedict
        else:
            self.tkinter_vars = {}  
            self.top.instance_dict = {}
            
        self.recent_files_path = pemConf.userdir and os.path.join(
                pemConf.userdir, 'recent-files.lst')

        self.prompt_last_line = ''


        # ---------------------------------------------------------------------
        # SUBSYSTEM: GLOBAL TOOLBAR ARCHITECTURE
        # ---------------------------------------------------------------------
        if flist and hasattr(flist, 'notebook') and flist.notebook and not getattr(self, 'is_shell', False):
            # For the main IDE, we only want ONE toolbar hovering above the Notebook.
            if not hasattr(self.top, 'global_toolbar'):
                self.top.global_toolbar = Frame(self.top, relief=FLAT, borderwidth=0)
                try:
                    # Pack it explicitly BEFORE the notebook so it renders at the very top!
                    self.top.global_toolbar.pack(side=TOP, fill=X, pady=0, before=flist.notebook)
                except TclError:
                    self.top.global_toolbar.pack(side=TOP, fill=X, pady=0)
                
                self.toolbar_frame = self.top.global_toolbar
                self.create_toolbar()
                self.top.current_editor = self
            else:
                # If the global toolbar already exists, just link to it and skip recreation
                self.toolbar_frame = self.top.global_toolbar
        else:
            # The standalone Console still gets its own isolated local toolbar
            self.toolbar_frame = Frame(self.main_container, relief=FLAT, borderwidth=0)
            self.toolbar_frame.pack(side=TOP, fill=X, pady=0)
            self.create_toolbar()


        # ---------------------------------------------------------------------
        # SUBSYSTEM: SPLIT-PANE UI
        # ---------------------------------------------------------------------
        # Dynamically choose the best 1-pixel border strategy based on the OS
        if sys.platform == 'darwin':
            # Mac prefers the highlight ring hack for flat borders
            frame_opts = {'highlightbackground': 'gray75', 'highlightthickness': 1}
        else:
            # Windows and Linux prefer native solid relief
            frame_opts = {'relief': 'solid', 'borderwidth': 1}

        if not self.is_shell:
            # Code Editors receive a top pane (code) and a bottom pane (output)

            self.paned_window = PanedWindow(self.main_container, orient=VERTICAL)
            self.paned_window.pack(side=TOP, fill=BOTH, expand=1)

            # Apply the native border to the top wrapper pane
            self.editor_pane = Frame(self.paned_window, **frame_opts)
            self.paned_window.add(self.editor_pane, weight=4)

            # The Code Editor goes INSIDE the wrapper
            self.text_frame = text_frame = Frame(self.editor_pane)
        else:
            # The standalone Interactive Console gets the same border treatment
            self.text_frame = text_frame = Frame(self.main_container, **frame_opts)

        self.vbar = vbar = Scrollbar(text_frame, name='vbar')
        self.hbar = hbar = Scrollbar(text_frame, name='hbar', orient='horizontal')
        width = pemConf.GetOption('main', 'EditorWindow', 'width', type='int')
        text_options = {
                'name': 'text',
                'padx': 5,
                'wrap': 'none',
                'borderwidth': 0,             # <--- NEW: Remove native Tk border
                'relief': 'flat',             # <--- NEW: Flatten 3D sunken shadow
                'highlightthickness': 0,
                'width': width,
                'tabstyle': 'wordprocessor',  
                'height': pemConf.GetOption(
                        'main', 'EditorWindow', 'height', type='int'),
                }
        self.text = text = MultiCallCreator(Text)(text_frame, **text_options)
        self.top.focused_widget = self.text

        self.createmenubar()
        self.apply_bindings()


        # Apply specific deletion rules based on window architecture type
        if not (flist and hasattr(flist, 'notebook') and flist.notebook and not self.is_shell):
            self.top.protocol("WM_DELETE_WINDOW", self.close)
            
        # RESTORE GEOMETRY:
        # We call this unconditionally so every new tab can load its sash position.
        # The method internally prevents the main window from resizing more than once.
        self.restoreWindowGeometry()

        self.top.bind("<<close-window>>", self.close_event)
        text.bind('<<close-window>>', self.close_event)
            
        if macosx.isAquaTk():
            text.bind("<Control-Button-1>",self.right_menu_event)
            text.bind("<2>", self.right_menu_event)
        else:
            text.bind("<3>",self.right_menu_event)

        text.bind('<MouseWheel>', wheel_event)
        if text._windowingsystem == 'x11':
            text.bind('<Button-4>', wheel_event)
            text.bind('<Button-5>', wheel_event)

        # Drag-select past the visible area auto-scrolls in that direction so
        # the selection can extend offscreen.  See _update_auto_scroll.
        self._auto_scroll_id      = None
        self._auto_scroll_dx      = 0
        self._auto_scroll_dy      = 0
        self._auto_scroll_clamp_x = 0
        self._auto_scroll_clamp_y = 0
        text.bind('<B1-Motion>',       self._update_auto_scroll, add='+')
        text.bind('<ButtonRelease-1>', self._cancel_auto_scroll, add='+')

        # --- FONT ZOOM BINDINGS (Main Editor) ---
        text.bind('<Control-MouseWheel>', self.zoom_font)
        if sys.platform == 'darwin':                             
            text.bind('<Command-MouseWheel>', self.zoom_font)
            text.bind('<Option-MouseWheel>', self.zoom_font)       # failsafe
            
        if text.tk.call('tk', 'windowingsystem') == 'x11':
            text.bind('<Control-Button-4>', self.zoom_font)
            text.bind('<Control-Button-5>', self.zoom_font)

        text.bind('<Configure>', self.handle_winconfig)
        text.bind("<<cut>>", self.cut)
        text.bind("<<copy>>", self.copy)
        text.bind("<<paste>>", self.paste)
        text.bind("<<center-insert>>", self.center_insert_event)
        text.bind("<<jythonmusic-docs>>", self.jythonmusic_docs)
        text.bind("<<python-docs>>", self.python_docs)
        text.bind("<<about-pem>>", self.about_dialog)
        text.bind("<<open-config-dialog>>", self.config_dialog)
        text.bind("<<open-module>>", self.open_module_event)
        text.bind("<<do-nothing>>", lambda event: "break")
        text.bind("<<select-all>>", self.select_all)
        text.bind("<<remove-selection>>", self.remove_selection)
        text.bind("<<find>>", self.find_event)
        text.bind("<<find-again>>", self.find_again_event)
        text.bind("<<find-in-files>>", self.find_in_files_event)
        text.bind("<<find-selection>>", self.find_selection_event)
        text.bind("<<replace>>", self.replace_event)
        text.bind("<<goto-line>>", self.goto_line_event)
        text.bind("<<smart-backspace>>",self.smart_backspace_event)
        text.bind("<<newline-and-indent>>",self.newline_and_indent_event)
        text.bind("<<smart-indent>>",self.smart_indent_event)
        
        self.fregion = fregion = self.FormatRegion(self)
        text.bind("<<indent-region>>", fregion.indent_region_event)
        text.bind("<<dedent-region>>", fregion.dedent_region_event)
        text.bind("<<comment-region>>", fregion.comment_region_event)
        text.bind("<<uncomment-region>>", fregion.uncomment_region_event)
        text.bind("<<toggle-comment>>", fregion.toggle_comment_event)
        text.bind("<<tabify-region>>", fregion.tabify_region_event)
        text.bind("<<untabify-region>>", fregion.untabify_region_event)
        
        indents = self.Indents(self)
        text.bind("<<toggle-tabs>>", indents.toggle_tabs_event)
        text.bind("<<change-indentwidth>>", indents.change_indentwidth_event)
        text.bind("<Left>", self.move_at_edge_if_selection(0))
        text.bind("<Right>", self.move_at_edge_if_selection(1))
        text.bind("<<del-word-left>>", self.del_word_left)
        text.bind("<<del-word-right>>", self.del_word_right)
        text.bind("<<beginning-of-line>>", self.home_callback)

        if flist:
            flist.inversedict[self] = key
            if key:
                flist.dict[key] = self
            text.bind("<<open-new-window>>", self.new_callback)
            if sys.platform == 'darwin':
                text.event_add("<<open-new-window>>", "<Command-t>")
            else:
                text.event_add("<<open-new-window>>", "<Control-t>")
            text.bind("<<close-all-windows>>", self.flist.close_all_callback)
            text.bind("<<save-all-windows>>", self.save_all_windows_event)
            text.bind("<<quit>>", self.quit_event)
            text.bind("<<open-class-browser>>", self.open_module_browser)
            text.bind("<<open-path-browser>>", self.open_path_browser)

        self.set_status_bar()

        self._current_line_number = None
        self._update_current_line_color()
        text.bind("<<set-line-and-column>>", self._highlight_current_line, add='+')

        text_frame.pack(side=LEFT, fill=BOTH, expand=1)
        text_frame.rowconfigure(1, weight=1)
        text_frame.columnconfigure(1, weight=1)

        vbar['command'] = self.handle_yview
        vbar.grid(row=1, column=2, sticky=NSEW)
        text['yscrollcommand'] = vbar.set

        hbar['command'] = text.xview
        hbar.grid(row=2, column=1, sticky=EW)
        text['xscrollcommand'] = hbar.set

        text['font'] = pemConf.GetFont(self.root, 'main', 'EditorWindow')
        text.grid(row=1, column=1, sticky=NSEW)
        text.focus_set()
        self.set_width()

        # ---------------------------------------------------------------------
        # SUBSYSTEM: INTEGRATED OUTPUT CONSOLE
        # ---------------------------------------------------------------------
        if not self.is_shell:
            # Dynamically choose the best 1-pixel border strategy based on the OS
            if sys.platform == 'darwin':
                # Mac prefers the highlight ring hack for flat borders
                frame_opts = {'highlightbackground': 'gray75', 'highlightthickness': 1}
            else:
                # Windows and Linux prefer native solid relief
                frame_opts = {'relief': 'solid', 'borderwidth': 1}
                
            self.output_frame = output_frame = Frame(self.paned_window, **frame_opts)
            
            # ttk.PanedWindow.add() accepts only 'weight' (not padding etc.).
            self.paned_window.add(output_frame, weight=1)

            # Both panes now exist — sash index 0 is valid. Apply the saved sash
            # position so the first paint shows the correct ratio. Done here
            # rather than in restoreWindowGeometry() because that runs earlier
            # in __init__, before output_frame has been added.
            if not getattr(self, 'is_shell', False):
                target_sash = pemConf.GetOption('main', 'EditorWindow',
                                                    'sash-position', type='int',
                                                    default=None, warn_on_default=False)
                if target_sash and target_sash > 10:
                    self.paned_window.update_idletasks()
                    applied = False
                    try:
                        if (self.paned_window.winfo_exists() and
                            self.paned_window.winfo_height() >= target_sash + 30):
                            self.paned_window.sashpos(0, target_sash)
                            applied = True
                    except TclError:
                        pass

                    if not applied:
                        def _apply_sash(retries=15, t=target_sash):
                            try:
                                if not self.paned_window.winfo_exists():
                                    return
                                if self.paned_window.winfo_height() < t + 30:
                                    if retries > 0:
                                        self.paned_window.after(20,
                                            lambda: _apply_sash(retries - 1, t))
                                    return
                                self.paned_window.sashpos(0, t)
                            except TclError:
                                pass
                        self.paned_window.after_idle(_apply_sash)

                # Save only on real sash drags.
                self.paned_window.bind('<ButtonRelease-1>',
                                        self._save_sash_position, add='+')


            self.out_vbar = Scrollbar(output_frame, name='out_vbar')
            self.out_hbar = Scrollbar(output_frame, name='out_hbar', orient='horizontal')

            out_options = {
                'name': 'output_text',
                'padx': 5,
                'wrap': 'none',
                'highlightthickness': 0,
                'height': 6,          
                'state': 'disabled',  
                'bg': '#f8f9fa',
                'fg': '#003399'       # deep blue for stdout; stderr uses the "error" tag
            }

            self.output_text = Text(output_frame, **out_options)
            self.output_text.tag_config("error", foreground="#d32f2f")

            output_frame.rowconfigure(0, weight=1)
            output_frame.columnconfigure(0, weight=1)

            self.out_vbar['command'] = self.output_text.yview
            self.out_vbar.grid(row=0, column=1, sticky=NS)
            self.output_text['yscrollcommand'] = self.out_vbar.set

            self.out_hbar['command'] = self.output_text.xview
            self.out_hbar.grid(row=1, column=0, sticky=EW)
            self.output_text['xscrollcommand'] = self.out_hbar.set

            initial_font = pemConf.GetFont(self.root, 'main', 'EditorWindow')
            self.output_text.configure(font=initial_font)
            self.output_text.grid(row=0, column=0, sticky=NSEW)

            # --- FONT ZOOM BINDINGS (Output Pane) ---
            self.output_text.bind('<Control-MouseWheel>', self.zoom_font)
            if sys.platform == 'darwin':                       
                self.output_text.bind('<Command-MouseWheel>', self.zoom_font)
                self.output_text.bind('<Option-MouseWheel>', self.zoom_font)
                
            if self.output_text.tk.call('tk', 'windowingsystem') == 'x11':
                self.output_text.bind('<Control-Button-4>', self.zoom_font)
                self.output_text.bind('<Control-Button-5>', self.zoom_font)

        else:

            # Nullify attributes to prevent routing crashes
            self.output_text = None
            self.output_frame = None

        usespaces = pemConf.GetOption('main', 'Indent',
                                       'use-spaces', type='bool')
        self.usetabs = not usespaces

        self.tabwidth = 8    
        self.indentwidth = self.tabwidth
        self.set_notabs_indentwidth()

        if not hasattr(pemConf, 'blink_off_time'):
            pemConf.blink_off_time = self.text['insertofftime']
        self.update_cursor_blink()

        self.num_context_lines = 50, 500, 5000000
        self.per = per = self.Percolator(text)
        self.undo = undo = self.UndoDelegator()
        per.insertfilter(undo)
        text.undo_block_start = undo.undo_block_start
        text.undo_block_stop = undo.undo_block_stop
        undo.set_saved_change_hook(self.saved_change_hook)
        
        self.io = io = self.IOBinding(self)
        io.set_filename_change_hook(self.filename_change_hook)
        io.print_window = self.print_window  # use native OS print dialog
        self.good_load = False
        self.set_indentation_params(False)
        self.color = None 
        self.code_context = None 
        self.line_numbers = None 
        
        if filename:
            if os.path.exists(filename) and not os.path.isdir(filename):
                if io.loadfile(filename):
                    self.good_load = True
                    is_py_src = self.ispythonsource(filename)
                    self.set_indentation_params(is_py_src)
            else:
                io.set_filename(filename)
                self.good_load = True

        self.ResetColorizer()
        self.saved_change_hook()
        self.update_recent_files_list()
        self.load_extensions()
        
        menu = self.menudict.get('window')
        if menu:
            end = menu.index("end")
            if end is None:
                end = -1
            if end >= 0:
                menu.add_separator()
                end = end + 1
            self.wmenu_end = end
            window.register_callback(self.postwindowsmenu)

        self.askinteger = simpledialog.askinteger
        self.askyesno = messagebox.askyesno
        self.showerror = messagebox.showerror

        text.event_add('<<paren-closed>>', '<KeyRelease-parenright>',
                       '<KeyRelease-bracketright>', '<KeyRelease-braceright>')

        text.bind("<<format-paragraph>>",
                  self.FormatParagraph(self).format_paragraph_event)
        parenmatch = self.ParenMatch(self)
        text.bind("<<flash-paren>>", parenmatch.flash_paren_event)
        text.bind("<<paren-closed>>", parenmatch.paren_closed_event)
        scriptbinding = ScriptBinding(self)
        text.bind("<<check-module>>", scriptbinding.check_module_event)
        text.bind("<<run-module>>", scriptbinding.run_module_event)
        text.bind("<<run-custom>>", scriptbinding.run_custom_event)
        text.bind("<<run-selection>>", scriptbinding.run_selection_event)
        text.bind("<<run-current-line>>", scriptbinding.run_current_line_event)
        text.bind("<<run-current-paragraph>>", scriptbinding.run_current_paragraph_event)
        text.bind("<<create-executable>>", self.create_executable_event)
        text.bind("<<do-rstrip>>", self.Rstrip(self).do_rstrip)
        text.bind("<<zoom-height>>", self.ZoomHeight(self).zoom_height_event)
        text.bind("<<print-window>>", self.print_window)

        # Register Ctrl+P / Cmd+P as the print keyboard shortcut
        if sys.platform == 'darwin':
            text.event_add("<<print-window>>", "<Command-p>")
            _print_accel = "Cmd+P"
        else:
            text.event_add("<<print-window>>", "<Control-p>")
            _print_accel = "Ctrl+P"

        # Display the shortcut on the File ▸ Print menu item
        file_menu = self.menudict.get('file')
        if file_menu:
            end = file_menu.index(END)
            if end is not None:
                for i in range(end + 1):
                    try:
                        if file_menu.type(i) == 'command':
                            lbl = file_menu.entrycget(i, 'label')
                            if 'print' in lbl.lower():
                                file_menu.entryconfig(i, accelerator=_print_accel)
                                break
                    except (TclError, ValueError):
                        pass
        
        if self.allow_code_context:
            self.code_context = self.CodeContext(self)
            text.bind("<<toggle-code-context>>",
                      self.code_context.toggle_code_context_event)
            if pemConf.GetOption('main', 'EditorWindow',
                                  'code-context-default', type='bool', default=False):
                self.code_context.toggle_code_context_event()
        else:
            self.update_menu_state('options', '*ode*ontext', 'disabled')

        if self.allow_line_numbers:
            self.line_numbers = self.LineNumbers(self)
            if pemConf.GetOption('main', 'EditorWindow',
                                  'line-numbers-default', type='bool'):
                self.toggle_line_numbers_event()
            text.bind("<<toggle-line-numbers>>", self.toggle_line_numbers_event)
        else:
            self.update_menu_state('options', '*ine*umbers', 'disabled')

        # ---------------------------------------------------------------------
        # SUBSYSTEM: STARTUP BOOT SEQUENCE
        # Safely spawn the Interactive Console in the background asynchronously.
        # ---------------------------------------------------------------------
        if self.flist and not self.is_shell:
            if not getattr(self.flist, '_startup_console_booted', False):
                self.flist._startup_console_booted = True
                

                def _silent_startup_boot():
                    try:
                        if not self.text or not self.text.winfo_exists():
                            return

                        from pem import pyshell
                        if not getattr(self.flist, 'pyshell', None):

                            shell = pyshell.PyShell(self.flist)   # already born withdrawn, no menu attached
                            self.flist.pyshell = shell
                            shell.begin()

                            if self.text and self.text.winfo_exists():
                                self.text.focus_set()

                    except (AttributeError, TclError):
                        # Shutdown race: editor or its widgets were torn down while the shell
                        # was still booting. Nothing to clean up — the close path handles it.
                        pass
                    except Exception:
                        import traceback
                        traceback.print_exc()

                # Defer the (relatively expensive) console boot past the first idle cycle
                # so the editor renders and becomes interactive without waiting on the
                # subprocess spawn and shell widget construction.
                self.startup_timer = self.text.after(250, _silent_startup_boot)


    # -------------------------------------------------------------------------
    # CORE INTERFACE METHODS
    # -------------------------------------------------------------------------
    def handle_winconfig(self, event=None):
        self.set_width()

    def set_width(self):
        text = self.text
        inner_padding = sum(map(text.tk.getint, [text.cget('border'),
                                                 text.cget('padx')]))
        pixel_width = text.winfo_width() - 2 * inner_padding

        zero_char_width = \
            Font(text, font=text.cget('font')).measure('0')
        self.width = pixel_width // zero_char_width

    def new_callback(self, event):
        dirname, basename = self.io.defaultfilename()
        new_edit = self.flist.new(dirname)
        if new_edit:
            new_edit._user_created = True
        return "break"

    def home_callback(self, event):
        if (event.state & 4) != 0 and event.keysym == "Home":
            return None
        if self.text.index("iomark") and \
           self.text.compare("iomark", "<=", "insert lineend") and \
           self.text.compare("insert linestart", "<=", "iomark"):
            insertpt = int(self.text.index("iomark").split(".")[1])
        else:
            line = self.text.get("insert linestart", "insert lineend")
            for insertpt in range(len(line)):
                if line[insertpt] not in (' ','\t'):
                    break
            else:
                insertpt=len(line)
        lineat = int(self.text.index("insert").split('.')[1])
        if insertpt == lineat:
            insertpt = 0
        dest = "insert linestart+"+str(insertpt)+"c"
        if (event.state&1) == 0:
            self.text.tag_remove("sel", "1.0", "end")
        else:
            if not self.text.index("sel.first"):
                self.text.mark_set("my_anchor", "insert")
            else:
                if self.text.compare(self.text.index("sel.first"), "<",
                                     self.text.index("insert")):
                    self.text.mark_set("my_anchor", "sel.first") 
                else:
                    self.text.mark_set("my_anchor", "sel.last") 
            first = self.text.index(dest)
            last = self.text.index("my_anchor")
            if self.text.compare(first,">",last):
                first,last = last,first
            self.text.tag_remove("sel", "1.0", "end")
            self.text.tag_add("sel", first, last)
        self.text.mark_set("insert", dest)
        self.text.see("insert")
        return "break"

    def set_status_bar(self):
        # Attach the status bar and separator to the individual tab container, 
        # ensuring they are cleanly destroyed when the tab is closed.
        self.status_bar = self.MultiStatusBar(self.main_container)
        sep = Frame(self.main_container, height=1, borderwidth=1, background='grey75')
        
        if sys.platform == "darwin":
            self.status_bar.set_label('_padding1', '    ', side=RIGHT)
            
        self.status_bar.set_label('column', 'Col: ?', side=RIGHT)
        self.status_bar.set_label('line', 'Ln: ?', side=RIGHT)
        
        self.status_bar.pack(side=BOTTOM, fill=X)
        sep.pack(side=BOTTOM, fill=X)
        
        self.text.bind("<<set-line-and-column>>", self.set_line_and_column)
        self.text.event_add("<<set-line-and-column>>",
                            "<KeyRelease>", "<ButtonRelease>")
        self.text.after_idle(self.set_line_and_column)


    def set_line_and_column(self, event=None):
        line, column = self.text.index(INSERT).split('.')
        self.status_bar.set_label('column', 'Col: %s' % column)
        self.status_bar.set_label('line', 'Ln: %s' % line)


    def _highlight_current_line(self, event=None):
        if not self.allow_highlight_current_line:
            return

        enabled = pemConf.GetOption(
            'main', 'EditorWindow', 'highlight-current-line', type='bool', default=False)
        if not enabled:
            self.text.tag_remove("current-line", "1.0", "end")
            self._current_line_number = None
            return

        line = self.text.index("insert").split('.')[0]
        prevLine = self._current_line_number

        if prevLine is not None and prevLine != line:
            self.text.tag_remove("current-line", f"{prevLine}.0", f"{prevLine}.end+1c")

        self.text.tag_add("current-line", f"{line}.0", f"{line}.end+1c")
        self._current_line_number = line

    def _update_current_line_color(self):
        # -------------------------------------------------------------
        # SUBSYSTEM: CUSTOM LINE HIGHLIGHT
        # Apply a static, soft pale yellow (RGB: 255, 255, 170) to the 
        # current line to improve readability and cursor tracking.
        # -------------------------------------------------------------
        custom_highlight = "#ffffaa"
        
        self.text.tag_configure("current-line", background=custom_highlight)
        
        # --- NEW: Explicitly force the mouse selection to be blue ---
        self.text.tag_configure("sel", background="#add6ff") 
        
        # Ensure the selection highlight ('sel') always renders ON TOP of 
        # the current-line highlight so users can still see what they highlight.
        self.text.tag_lower("current-line", "sel")

    
    menu_specs = [
        ("file", "_File"),
        ("edit", "_Edit"),
        ("run", "_Run"),
        ("window", "_Window"),
        ("help", "_Help"),
    ]

    def createmenubar(self):
        mbar = self.menubar
        self.menudict = menudict = {}
        for name, label in self.menu_specs:
            underline, label = prepstr(label)
            postcommand = getattr(self, f'{name}_menu_postcommand', None)
            menudict[name] = menu = Menu(mbar, name=name, tearoff=0,
                                         postcommand=postcommand)
            mbar.add_cascade(label=label, menu=menu, underline=underline)
        if macosx.isCarbonTk():
            menudict['application'] = menu = Menu(mbar, name='apple',
                                                  tearoff=0)
            mbar.add_cascade(label='PEM', menu=menu)
        self.fill_menus()
        self.recent_files_menu = Menu(self.menubar, tearoff=0)
        if 'file' in self.menudict:
            self.menudict['file'].insert_cascade(2, label='Open Recent',
                                                 underline=5,
                                                 menu=self.recent_files_menu)
        self.base_helpmenu_length = self.menudict['help'].index(END)
        self.reset_help_menu_entries()


    def run_menu_postcommand(self):
        """
        Auto-invoked every time the Run menu is about to open. Updates the
        Show/Hide Console entry to reflect the console's current visibility,
        so the label is always correct regardless of how the state was last
        changed (toolbar, menu, window-close, etc.).
        """

        #print(f"[run-menu] postcommand fired on editor={id(self)} "   # debug
        #f"flist.pyshell={getattr(self.flist, 'pyshell', None)}")

        try:
            run_menu = self.menudict.get('run')
            if not run_menu:
                return

            shell = getattr(self.flist, 'pyshell', None)
            is_visible = (
                shell is not None
                and hasattr(shell, 'top')
                and shell.top.winfo_exists()
                and shell.top.state() == 'normal'
            )
            new_label = "Hide Console" if is_visible else "Show Console"

            # Find the entry whose label mentions "Console" and rewrite it.
            # Substring-match handles "Show _Console" / "Hide _Console"
            # variations across platforms (Tk may keep or strip the
            # mnemonic underscore depending on the platform).
            last = run_menu.index('end')
            if last is None:
                return
            for i in range(last + 1):
                try:
                    if run_menu.type(i) != 'command':
                        continue
                    label = run_menu.entrycget(i, 'label')
                    if 'Console' in label:
                        run_menu.entryconfig(i, label=new_label)
                        break
                except TclError:
                    continue
        except (AttributeError, TclError):
            pass


    def load_toolbar_icon(self, icon_name, btn_size=26):
        # editor.py lives in pem/editing/; icons are in pem/icons/.
        icondir = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                               'icons', 'toolbar')
        use_dark = False
        if sys.platform == 'darwin':
            from pem import macosx
            if macosx.isDarkMode():
                use_dark = True

        if not hasattr(self, '_toolbar_icons'):
            self._toolbar_icons = []

        def _candidate_paths(extensions):
            """Yield (dark_path, normal_path) pairs for each extension."""
            for ext in extensions:
                if use_dark:
                    dark_path = os.path.join(icondir, icon_name + '_dark' + ext)
                    if os.path.exists(dark_path):
                        yield dark_path
                normal_path = os.path.join(icondir, icon_name + ext)
                if os.path.exists(normal_path):
                    yield normal_path

        # Strategy 1: Use PIL for high-quality resizing (supports more formats)
        try:
            from PIL import Image, ImageTk
            for icon_path in _candidate_paths(['.png', '.gif', '.ico', '.bmp', '.jpg', '.jpeg']):
                try:
                    pil_img = Image.open(icon_path)
                    if pil_img.mode != 'RGBA':
                        pil_img = pil_img.convert('RGBA')
                    pil_img = pil_img.resize((btn_size, btn_size), Image.LANCZOS)
                    img = ImageTk.PhotoImage(pil_img, master=self.root)
                    self._toolbar_icons.append(img)
                    return img
                except Exception:
                    pass
        except ImportError:
            pass

        # Strategy 2: Fall back to tkinter's built-in PhotoImage (.png/.gif only)
        for icon_path in _candidate_paths(['.png', '.gif']):
            try:
                img = PhotoImage(file=icon_path, master=self.root)
                subsample = max(1, img.width() // btn_size)
                img = img.subsample(subsample, subsample)
                self._toolbar_icons.append(img)
                return img
            except Exception:
                pass

        return None

    def create_toolbar_button(self, parent, icon, command, btn_size, btn_padx, btn_pady, side=LEFT):
        if sys.platform == 'darwin':
            toolbar_bg = self.toolbar_frame.cget('bg')
            btn = Canvas(parent, width=btn_size, height=btn_size,
                         highlightthickness=0, relief=FLAT,
                         bg=toolbar_bg)
            x = btn_size // 2
            y = btn_size // 2
            btn.create_image(x, y, image=icon, anchor='center', tags='icon')
            btn.bind('<Button-1>', lambda e: command())
            btn._original_bg = toolbar_bg
            def on_enter(e):
                pass
            def on_leave(e):
                btn.config(bg=btn._original_bg)
            btn.bind('<Enter>', on_enter)
            btn.bind('<Leave>', on_leave)
            btn.pack(side=side, padx=btn_padx, pady=btn_pady)
            return btn
        else:
            btn = Button(parent, image=icon, relief=FLAT,
                         borderwidth=0, command=command,
                         bg=self.toolbar_frame.cget('bg'),
                         activebackground=self.toolbar_frame.cget('bg'),
                         highlightbackground=self.toolbar_frame.cget('bg'))
            btn.pack(side=side, padx=btn_padx, pady=btn_pady)
            return btn

    def create_toolbar(self):
        from pem.dialogs.tooltip import Hovertip
        import math

        btn_size = 26
        btn_padx = 4   
        btn_pady = 3   
        sep_padx = 8   

        if not self.is_shell:
            icon = self.load_toolbar_icon('play', btn_size)
            if icon:
                run_btn = self.create_toolbar_button(self.toolbar_frame, icon, self.toolbar_run,
                                                   btn_size, btn_padx, btn_pady)
                # Stash the button + (idle, running) glyphs so FileList.set_run_indicator()
                # can show a "running" state on the shared toolbar while a script runs.
                self.top.global_run_button = run_btn
                self.top.global_run_icons = (icon, self.load_toolbar_icon('running', btn_size))
            else:
                run_btn = Canvas(self.toolbar_frame, width=btn_size, height=btn_size,
                               highlightthickness=0, relief=FLAT,
                               bg=self.toolbar_frame.cget('bg'))
                run_btn.create_polygon(10, 8, 10, 24, 24, 16, fill='black', tags='icon')
                run_btn.bind('<Button-1>', lambda e: self.toolbar_run())
                run_btn.pack(side=LEFT, padx=btn_padx, pady=btn_pady)
            Hovertip(run_btn, "Run (Ctrl+R)")

        if self.is_shell:
            icon = self.load_toolbar_icon('reset', btn_size)
            if icon:
                stop_btn = self.create_toolbar_button(self.toolbar_frame, icon, self.toolbar_reset,
                                                     btn_size, btn_padx, btn_pady)
            else:
                stop_btn = Canvas(self.toolbar_frame, width=btn_size, height=btn_size,
                                highlightthickness=0, relief=FLAT,
                                bg=self.toolbar_frame.cget('bg'))
                stop_btn.create_rectangle(9, 9, 23, 23, fill='black', outline='black', tags='icon')
                stop_btn.bind('<Button-1>', lambda e: self.toolbar_reset())
                stop_btn.pack(side=LEFT, padx=btn_padx, pady=btn_pady)
            Hovertip(stop_btn, "Reset Console")
        else:
            icon = self.load_toolbar_icon('stop', btn_size)
            if icon:
                stop_btn = self.create_toolbar_button(self.toolbar_frame, icon, self.toolbar_stop,
                                                     btn_size, btn_padx, btn_pady)
            else:
                stop_btn = Canvas(self.toolbar_frame, width=btn_size, height=btn_size,
                                highlightthickness=0, relief=FLAT,
                                bg=self.toolbar_frame.cget('bg'))
                stop_btn.create_rectangle(9, 9, 23, 23, fill='black', outline='black', tags='icon')
                stop_btn.bind('<Button-1>', lambda e: self.toolbar_stop())
                stop_btn.pack(side=LEFT, padx=btn_padx, pady=btn_pady)
            Hovertip(stop_btn, "Stop")

        if not self.is_shell:
            sep1 = Frame(self.toolbar_frame, width=1, height=btn_size-4, bg='gray70', relief=FLAT)
            sep1.pack(side=LEFT, padx=sep_padx, pady=btn_pady)

            icon = self.load_toolbar_icon('new_file', btn_size)
            if icon:
                new_btn = self.create_toolbar_button(self.toolbar_frame, icon, self.toolbar_new_file,
                                                   btn_size, btn_padx, btn_pady)
            else:
                new_btn = Canvas(self.toolbar_frame, width=btn_size, height=btn_size,
                                highlightthickness=0, relief=FLAT,
                                bg=self.toolbar_frame.cget('bg'))
                new_btn.create_rectangle(10, 6, 24, 26, outline='black', width=2, fill='white', tags='icon')
                new_btn.create_line(18, 6, 18, 13, width=2, fill='black', tags='icon')
                new_btn.create_line(18, 13, 24, 13, width=2, fill='black', tags='icon')
                new_btn.bind('<Button-1>', lambda e: self.toolbar_new_file())
                new_btn.pack(side=LEFT, padx=btn_padx, pady=btn_pady)
            Hovertip(new_btn, "New (Ctrl+N)")

            icon = self.load_toolbar_icon('open_file', btn_size)
            if icon:
                open_btn = self.create_toolbar_button(self.toolbar_frame, icon, self.toolbar_open_file,
                                                    btn_size, btn_padx, btn_pady)
            else:
                open_btn = Canvas(self.toolbar_frame, width=btn_size, height=btn_size,
                                 highlightthickness=0, relief=FLAT,
                                 bg=self.toolbar_frame.cget('bg'))
                open_btn.create_rectangle(8, 12, 24, 24, outline='black', width=2, fill='white', tags='icon')
                open_btn.create_polygon(8, 12, 12, 12, 13, 9, 17, 9, 18, 12, fill='white', outline='black', width=2, tags='icon')
                open_btn.bind('<Button-1>', lambda e: self.toolbar_open_file())
                open_btn.pack(side=LEFT, padx=btn_padx, pady=btn_pady)
            Hovertip(open_btn, "Open (Ctrl+O)")

            icon = self.load_toolbar_icon('save', btn_size)
            if icon:
                save_btn = self.create_toolbar_button(self.toolbar_frame, icon, self.toolbar_save,
                                                    btn_size, btn_padx, btn_pady)
            else:
                save_btn = Canvas(self.toolbar_frame, width=btn_size, height=btn_size,
                                 highlightthickness=0, relief=FLAT,
                                 bg=self.toolbar_frame.cget('bg'))
                save_btn.create_rectangle(9, 6, 23, 26, outline='black', width=2, fill='white', tags='icon')
                save_btn.create_rectangle(11, 20, 21, 26, outline='black', width=1, fill='black', tags='icon')
                save_btn.create_line(13, 6, 13, 11, width=2, fill='black', tags='icon')
                save_btn.create_line(19, 6, 19, 11, width=2, fill='black', tags='icon')
                save_btn.bind('<Button-1>', lambda e: self.toolbar_save())
                save_btn.pack(side=LEFT, padx=btn_padx, pady=btn_pady)
            Hovertip(save_btn, "Save (Ctrl+S)")

            icon = self.load_toolbar_icon('create_exe', btn_size)
            if icon:
                exe_btn = self.create_toolbar_button(self.toolbar_frame, icon, self.toolbar_create_executable,
                                                     btn_size, btn_padx, btn_pady)
            else:
                exe_btn = Canvas(self.toolbar_frame, width=btn_size, height=btn_size,
                                 highlightthickness=0, relief=FLAT,
                                 bg=self.toolbar_frame.cget('bg'))
                exe_btn.create_rectangle(7, 8, 25, 24, outline='black', width=2, fill='white', tags='icon')
                exe_btn.create_polygon(13, 12, 13, 20, 20, 16, fill='black', tags='icon')
                exe_btn.bind('<Button-1>', lambda e: self.toolbar_create_executable())
                exe_btn.pack(side=LEFT, padx=btn_padx, pady=btn_pady)
            Hovertip(exe_btn, "Create Executable")

            sep2 = Frame(self.toolbar_frame, width=1, height=btn_size-4, bg='gray70', relief=FLAT)
            sep2.pack(side=LEFT, padx=sep_padx, pady=btn_pady)

            icon = self.load_toolbar_icon('console', btn_size)
            if icon:
                shell_btn = self.create_toolbar_button(self.toolbar_frame, icon, self.toolbar_shell,
                                                     btn_size, btn_padx, btn_pady)
            else:
                shell_btn = Canvas(self.toolbar_frame, width=btn_size, height=btn_size,
                                  highlightthickness=0, relief=FLAT,
                                  bg=self.toolbar_frame.cget('bg'))
                shell_btn.create_rectangle(6, 8, 26, 24, outline='black', width=2, fill='white', tags='icon')
                shell_btn.create_text(16, 16, text='>', fill='black', font=('Courier', 12, 'bold'), tags='icon')
                shell_btn.bind('<Button-1>', lambda e: self.toolbar_shell())
                shell_btn.pack(side=LEFT, padx=btn_padx, pady=btn_pady)
            Hovertip(shell_btn, "Console")

            sep3 = Frame(self.toolbar_frame, width=1, height=btn_size-4, bg='gray70', relief=FLAT)
            sep3.pack(side=LEFT, padx=sep_padx, pady=btn_pady)

            icon = self.load_toolbar_icon('preferences', btn_size)
            if icon:
                pref_btn = self.create_toolbar_button(self.toolbar_frame, icon, self.toolbar_preferences,
                                                    btn_size, btn_padx, btn_pady)
            else:
                pref_btn = Canvas(self.toolbar_frame, width=btn_size, height=btn_size,
                                 highlightthickness=0, relief=FLAT,
                                 bg=self.toolbar_frame.cget('bg'))
                pref_btn.create_oval(11, 11, 21, 21, outline='black', width=2, fill='white', tags='icon')
                pref_btn.create_oval(14, 14, 18, 18, outline='black', width=1, fill='black', tags='icon')
                for angle in [0, 45, 90, 135, 180, 225, 270, 315]:
                    x1 = 16 + 6 * math.cos(math.radians(angle))
                    y1 = 16 + 6 * math.sin(math.radians(angle))
                    x2 = 16 + 8 * math.cos(math.radians(angle))
                    y2 = 16 + 8 * math.sin(math.radians(angle))
                    pref_btn.create_line(x1, y1, x2, y2, width=2, fill='black', tags='icon')
                pref_btn.bind('<Button-1>', lambda e: self.toolbar_preferences())
                pref_btn.pack(side=LEFT, padx=btn_padx, pady=btn_pady)
            Hovertip(pref_btn, "Preferences")


    # --- GLOBAL TOOLBAR ROUTING ENGINE ---
    def get_active_editor(self):
        """Fetches the currently visible tab so the global toolbar clicks the right code."""
        if hasattr(self, 'top') and hasattr(self.top, 'current_editor') and self.top.current_editor:
            return self.top.current_editor
        return self

    def toolbar_run(self):
        editor = self.get_active_editor()
        editor.text.after(0, lambda: editor.text.event_generate("<<run-module>>"))

    def toolbar_stop(self):
        # Stop the running script by restarting its execution subprocess.
        # Deliberately does NOT close the Console window: closing it nulls
        # flist.pyshell and forces a slow rebuild on the next Run.
        active_editor = self.get_active_editor()
        flist = getattr(active_editor, 'flist', None)
        sh = getattr(flist, 'pyshell', None) if flist else None
        if sh and getattr(sh, 'interp', None) and getattr(sh.interp, 'rpcclt', None):
            try:
                sh.restart_shell()
            except Exception:
                pass

    def toolbar_new_file(self):
        active_editor = self.get_active_editor()
        # If an editor exists, route through it safely
        if active_editor and hasattr(active_editor, 'text') and active_editor.text and active_editor.text.winfo_exists():
            active_editor.text.event_generate("<<open-new-window>>")
        # If 0 tabs exist (empty workspace), bypass the routing and force a hard boot!
        elif hasattr(self, 'flist') and self.flist:
            new_edit = self.flist.new()
            if new_edit:
                new_edit._user_created = True

    def toolbar_open_file(self):
        active_editor = self.get_active_editor()
        if active_editor and hasattr(active_editor, 'text') and active_editor.text and active_editor.text.winfo_exists():
            active_editor.text.event_generate("<<open-window-from-file>>")
        elif hasattr(self, 'flist') and self.flist:
            self.flist.open()


    def toolbar_save(self):
        self.get_active_editor().text.event_generate("<<save-window>>")

    def toolbar_preferences(self):
        self.get_active_editor().text.event_generate("<<open-config-dialog>>")

    def toolbar_create_executable(self):
        builder = exebuilder.ExeBuilder(self.get_active_editor())
        builder.create_executable()

    def toolbar_shell(self):
        """Toggles the visibility of the interactive Python Console."""
        # Defer by one event-loop tick so macOS can finish routing the toolbar
        # click's focus event to the editor before we raise the console.
        # Without this, lift() races the OS and the console ends up behind.
        self.text.after(0, self.flist.toggle_shell)


    def postwindowsmenu(self):
        menu = self.menudict['window']
        end = menu.index("end")
        if end is None:
            end = -1
        if end > self.wmenu_end:
            menu.delete(self.wmenu_end+1, end)
        window.add_windows_to_menu(menu)

    def update_menu_label(self, menu, index, label):
        menuitem = self.menudict.get(menu)
        if not menuitem:
            return   
        if '*' in str(index):
            import fnmatch
            end = menuitem.index(END)
            if end is None:
                return
            end += 1
            for i in range(0, end):
                if menuitem.type(i) in ('command', 'checkbutton'):
                    item_label = menuitem.entrycget(i, 'label')
                    if fnmatch.fnmatch(item_label.lower(), str(index).lower()):
                        menuitem.entryconfig(i, label=label)
                        return
        else:
            menuitem.entryconfig(index, label=label)

    def update_menu_state(self, menu, index, state):
        menuitem = self.menudict.get(menu)
        if not menuitem:
            return   
        if '*' in str(index):
            import fnmatch
            end = menuitem.index(END)
            if end is None:
                return
            end += 1
            for i in range(0, end):
                if menuitem.type(i) in ('command', 'checkbutton'):
                    item_label = menuitem.entrycget(i, 'label')
                    if fnmatch.fnmatch(item_label.lower(), str(index).lower()):
                        menuitem.entryconfig(i, state=state)
                        return
        else:
            menuitem.entryconfig(index, state=state)

    def handle_yview(self, event, *args):
        if event == 'moveto':
            fraction = float(args[0])
            lines = (round(self.getlineno('end') * fraction) -
                     self.getlineno('@0,0'))
            event = 'scroll'
            args = (lines, 'units')
        self.text.yview(event, *args)
        return 'break'

    rmenu = None

    def right_menu_event(self, event):
        text = self.text
        newdex = text.index(f'@{event.x},{event.y}')
        try:
            in_selection = (text.compare('sel.first', '<=', newdex) and
                           text.compare(newdex, '<=',  'sel.last'))
        except TclError:
            in_selection = False
        if not in_selection:
            text.tag_remove("sel", "1.0", "end")
            text.mark_set("insert", newdex)
        if not self.rmenu:
            self.make_rmenu()
        rmenu = self.rmenu
        self.event = event
        iswin = sys.platform[:3] == 'win'
        if iswin:
            text.config(cursor="arrow")

        for item in self.rmenu_specs:
            try:
                label, eventname, verify_state = item
            except ValueError: 
                continue

            if verify_state is None:
                continue
            state = getattr(self, verify_state)()
            rmenu.entryconfigure(label, state=state)

        rmenu.tk_popup(event.x_root, event.y_root)
        if iswin:
            self.text.config(cursor="ibeam")
        return "break"

    rmenu_specs = [
        ("Close", "<<close-window>>", None),
    ]

    def make_rmenu(self):
        rmenu = Menu(self.text, tearoff=0)
        for item in self.rmenu_specs:
            label, eventname = item[0], item[1]
            if label is not None:

                def command(text=self.text, eventname=eventname):
                    text.event_generate(eventname)

                rmenu.add_command(label=label, command=command)
            else:
                rmenu.add_separator()
        self.rmenu = rmenu

    def rmenu_check_cut(self):
        return self.rmenu_check_copy()

    def rmenu_check_copy(self):
        try:
            indx = self.text.index('sel.first')
        except TclError:
            return 'disabled'
        else:
            return 'normal' if indx else 'disabled'

    def rmenu_check_paste(self):
        try:
            self.text.tk.call('tk::GetSelection', self.text, 'CLIPBOARD')
        except TclError:
            return 'disabled'
        else:
            return 'normal'

    def about_dialog(self, event=None):
        about.AboutDialog(self.top)
        return "break"

    def config_dialog(self, event=None):
        configdialog.ConfigDialog(self.top,'Preferences')
        return "break"

    def create_executable_event(self, event=None):
        builder = exebuilder.ExeBuilder(self)
        builder.create_executable()
        return "break"

    def jythonmusic_docs(self, event=None):
        if self.root:
            parent = self.root
        else:
            parent = self.top
        help.show_pemhelp(parent)
        return "break"

    def python_docs(self, event=None):
        if sys.platform[:3] == 'win':
            try:
                os.startfile(self.help_url)
            except OSError as why:
                messagebox.showerror(title='Document Start Failure',
                    message=str(why), parent=self.text)
        else:
            webbrowser.open(self.help_url)
        return "break"

    def print_window(self, event=None):
        """Print the current document using the native OS print dialog.

        Renders the source into a lightweight HTML page with line numbers,
        opens it in the default browser, and immediately triggers the
        browser's native print dialog.  This is non-blocking — the editor
        stays fully responsive — and works on every platform.
        """
        import html as _html
        import tempfile

        source = self.text.get("1.0", "end-1c")
        filename = self.short_title()

        # Build numbered, HTML-escaped source lines
        lines = source.split('\n')
        gutter = len(str(len(lines)))
        numbered = '\n'.join(
            f'{n:>{gutter}}  {_html.escape(line)}'
            for n, line in enumerate(lines, 1)
        )

        escaped_title = _html.escape(filename)
        page = (
            '<!DOCTYPE html>\n<html>\n<head>\n'
            f'<meta charset="utf-8"><title>Print – {escaped_title}</title>\n'
            '<style>\n'
            '  body { margin: 0.25in 0.25in; }\n'
            '  h4   { font-family: sans-serif; margin-bottom: 4pt; }\n'
            '  pre  { font-family: "Courier New", Courier, monospace;\n'
            '         font-size: 10pt; line-height: 1.5;\n'
            '         white-space: pre-wrap; word-wrap: break-word; }\n'
            '  @media print { h4 { font-size: 9pt; color: #999; } }\n'
            '</style>\n</head>\n'
            '<body onload="window.print()">\n'
            f'<h4>{escaped_title}</h4>\n<pre>{numbered}</pre>\n'
            '</body>\n</html>'
        )

        try:
            fd, path = tempfile.mkstemp(suffix='.html')
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(page)
            webbrowser.open('file:///' + os.path.abspath(path).replace('\\', '/'))
        except OSError as err:
            messagebox.showerror("Print Error", str(err), parent=self.text)

        return "break"

    def cut(self,event):
        self.text.event_generate("<<Cut>>")
        return "break"

    def copy(self,event):
        if not self.text.tag_ranges("sel"):
            return None
        self.text.event_generate("<<Copy>>")
        return "break"

    def paste(self,event):
        self.text.event_generate("<<Paste>>")
        self.text.see("insert")
        return "break"

    def select_all(self, event=None):
        self.text.tag_add("sel", "1.0", "end-1c")
        self.text.mark_set("insert", "1.0")
        self.text.see("insert")
        return "break"

    def remove_selection(self, event=None):
        self.text.tag_remove("sel", "1.0", "end")
        self.text.see("insert")
        return "break"

    def move_at_edge_if_selection(self, edge_index):
        self_text_index = self.text.index
        self_text_mark_set = self.text.mark_set
        edges_table = ("sel.first+1c", "sel.last-1c")
        def move_at_edge(event):
            if (event.state & 5) == 0: 
                try:
                    self_text_index("sel.first")
                    self_text_mark_set("insert", edges_table[edge_index])
                except TclError:
                    pass
        return move_at_edge

    def del_word_left(self, event):
        self.text.event_generate('<Meta-Delete>')
        return "break"

    def del_word_right(self, event):
        self.text.event_generate('<Meta-d>')
        return "break"

    def find_event(self, event):
        search.find(self.text)
        return "break"

    def find_again_event(self, event):
        search.find_again(self.text)
        return "break"

    def find_selection_event(self, event):
        search.find_selection(self.text)
        return "break"

    def find_in_files_event(self, event):
        grep.grep(self.text, self.io, self.flist)
        return "break"

    def replace_event(self, event):
        replace.replace(self.text)
        return "break"

    def goto_line_event(self, event):
        text = self.text
        lineno = query.Goto(
                text, "Go To Line",
                "Enter a positive integer\n"
                "('big' = end of file):"
                ).result
        if lineno is not None:
            text.tag_remove("sel", "1.0", "end")
            text.mark_set("insert", f'{lineno}.0')
            text.see("insert")
            self.set_line_and_column()
        return "break"

    def open_module(self):
        try:
            name = self.text.get("sel.first", "sel.last").strip()
        except TclError:
            name = ''
        file_path = query.ModuleName(
                self.text, "Open Module",
                "Enter the name of a Python module\n"
                "to search on sys.path and open:",
                name).result
        if file_path is not None:
            if self.flist:
                self.flist.open(file_path)
            else:
                self.io.loadfile(file_path)
        return file_path

    def open_module_event(self, event):
        self.open_module()
        return "break"

    def open_module_browser(self, event=None):
        filename = self.io.filename
        if not (self.__class__.__name__ == 'PyShellEditorWindow'
                and filename):
            filename = self.open_module()
            if filename is None:
                return "break"
        from pem.editing import browser
        browser.ModuleBrowser(self.root, filename)
        return "break"

    def open_path_browser(self, event=None):
        from pem.editing import pathbrowser
        pathbrowser.PathBrowser(self.root)
        return "break"

    def open_turtle_demo(self, event = None):
        import subprocess

        cmd = [sys.executable,
               '-c',
               'from turtledemo.__main__ import main; main()']
        subprocess.Popen(cmd, shell=False)
        return "break"

    def gotoline(self, lineno):
        if lineno is not None and lineno > 0:
            self.text.mark_set("insert", "%d.0" % lineno)
            self.text.tag_remove("sel", "1.0", "end")
            self.text.tag_add("sel", "insert", "insert +1l")
            self.center()

    def ispythonsource(self, filename):
        if not filename or os.path.isdir(filename):
            return True
        base, ext = os.path.splitext(os.path.basename(filename))
        if os.path.normcase(ext) in py_extensions:
            return True
        line = self.text.get('1.0', '1.0 lineend')
        return line.startswith('#!') and 'python' in line

    def close_hook(self):
        if self.flist:
            self.flist.unregister_maybe_terminate(self)
            self.flist = None

    def set_close_hook(self, close_hook):
        self.close_hook = close_hook

    def filename_change_hook(self):
        if self.flist:
            self.flist.filename_changed_edit(self)
        self.saved_change_hook()
        
        if hasattr(self.top, 'update_windowlist_registry'):
            self.top.update_windowlist_registry(self)
            
        self.ResetColorizer()

    def _addcolorizer(self):
        if self.color:
            return
        if self.ispythonsource(self.io.filename):
            self.color = self.ColorDelegator()
        if self.color:
            self.per.insertfilterafter(filter=self.color, after=self.undo)

    def _rmcolorizer(self):
        if not self.color:
            return
        self.color.removecolors()
        self.per.removefilter(self.color)
        self.color = None

    def ResetColorizer(self):
        self._rmcolorizer()
        self._addcolorizer()
        EditorWindow.color_config(self.text)

        self._update_current_line_color()
        self._current_line_number = None
        self._highlight_current_line()

        if self.code_context is not None:
            self.code_context.update_highlight_colors()

        if self.line_numbers is not None:
            self.line_numbers.update_colors()

    IDENTCHARS = string.ascii_letters + string.digits + "_"

    def colorize_syntax_error(self, text, pos):
        text.tag_add("ERROR", pos)
        char = text.get(pos)
        if char and char in self.IDENTCHARS:
            text.tag_add("ERROR", pos + " wordstart", pos)
        if '\n' == text.get(pos):   
            text.mark_set("insert", pos)
        else:
            text.mark_set("insert", pos + "+1c")
        text.see(pos)

    def update_cursor_blink(self):
        cursorblink = pemConf.GetOption(
                'main', 'EditorWindow', 'cursor-blink', type='bool')
        if not cursorblink:
            self.text['insertofftime'] = 0
        else:
            self.text['insertofftime'] = pemConf.blink_off_time

    def ResetFont(self):
        if self.code_context is not None:
            self.code_context.update_font()
        if self.line_numbers is not None:
            self.line_numbers.update_font()
        new_font = pemConf.GetFont(self.root, 'main', 'EditorWindow')
        self.text['font'] = new_font
        self.set_width()
        
        # Keep the bottom output pane on the same font as the editor.
        if getattr(self, 'output_text', None):
            self.output_text.configure(font=new_font)

    def zoom_font(self, event):
        """
        Dynamically adjust the font size using Ctrl + Mouse Wheel.
        This updates the configuration in memory, which allows the _close()
        method to automatically save the new preferred size to disk.
        """
        # 1. Determine scroll direction based on OS-specific event triggers
        if hasattr(event, 'num') and event.num in (4, 5):
            # Linux / X11 triggers
            direction = 1 if event.num == 4 else -1
        else:
            # Windows / Mac triggers
            direction = 1 if event.delta > 0 else -1

        # 2. Retrieve current font size directly from active memory
        current_size = pemConf.GetOption('main', 'EditorWindow', 'font-size', type='int', default=12)
        
        # 3. Calculate new size (clamped to readable extremes)
        new_size = max(6, min(current_size + direction, 72))

        if new_size != current_size:
            # Update the configuration in memory
            pemConf.SetOption('main', 'EditorWindow', 'font-size', str(new_size))
            
            # Instantly broadcast the font update to all active tabs and consoles
            for instance in self.top.instance_dict:
                instance.ResetFont()
                
        return "break" # Prevent the default text-scrolling behavior

    def _update_auto_scroll(self, event):
        """
        <B1-Motion> handler.  When the drag extends past the text widget's
        visible area, start (or maintain) an auto-scroll timer so a selection
        can extend offscreen.  When the cursor is back inside the widget,
        any running timer is cancelled.  No-op for in-bounds drags.
        """
        height = self.text.winfo_height()
        width  = self.text.winfo_width()

        overshoot_y = 0
        if event.y < 0:
            overshoot_y = event.y
        elif event.y >= height:
            overshoot_y = event.y - (height - 1)

        overshoot_x = 0
        if event.x < 0:
            overshoot_x = event.x
        elif event.x >= width:
            overshoot_x = event.x - (width - 1)

        if overshoot_x or overshoot_y:
            self._auto_scroll_dx      = overshoot_x
            self._auto_scroll_dy      = overshoot_y
            self._auto_scroll_clamp_x = max(0, min(width  - 1, event.x))
            self._auto_scroll_clamp_y = max(0, min(height - 1, event.y))
            if self._auto_scroll_id is None:
                self._tick_auto_scroll()
        else:
            self._cancel_auto_scroll()

    def _tick_auto_scroll(self):
        """
        Scrolls the view in the overshoot direction and extends the selection
        to the (clamped-to-widget) cursor position, then reschedules itself.
        After scrolling, the same screen coordinate addresses a newly-visible
        character, so tk::TextSelectTo grows the selection one line/column at
        a time — the same code path Tk's own <B1-Motion> binding uses.
        Scroll magnitude grows with how far past the edge the cursor is.
        """
        if self._auto_scroll_dy != 0:
            magnitude = max(1, abs(self._auto_scroll_dy) // 30)
            direction = 1 if self._auto_scroll_dy > 0 else -1
            self.text.yview_scroll(direction * magnitude, 'units')

        if self._auto_scroll_dx != 0:
            magnitude = max(1, abs(self._auto_scroll_dx) // 30)
            direction = 1 if self._auto_scroll_dx > 0 else -1
            self.text.xview_scroll(direction * magnitude, 'units')

        self.text.tk.call('tk::TextSelectTo', str(self.text),
                          self._auto_scroll_clamp_x, self._auto_scroll_clamp_y)

        self._auto_scroll_id = self.text.after(50, self._tick_auto_scroll)

    def _cancel_auto_scroll(self, event=None):
        """<ButtonRelease-1> handler — stops any pending auto-scroll tick."""
        if self._auto_scroll_id is not None:
            self.text.after_cancel(self._auto_scroll_id)
            self._auto_scroll_id = None

    def RemoveKeybindings(self):
        self.mainmenu.default_keydefs = keydefs = pemConf.GetCurrentKeySet()
        for event, keylist in keydefs.items():
            self.text.event_delete(event, *keylist)
        for extensionName in self.get_standard_extension_names():
            xkeydefs = pemConf.GetExtensionBindings(extensionName)
            if xkeydefs:
                for event, keylist in xkeydefs.items():
                    self.text.event_delete(event, *keylist)

    def ApplyKeybindings(self):
        self.mainmenu.default_keydefs = keydefs = pemConf.GetCurrentKeySet()
        self.apply_bindings()
        for extensionName in self.get_standard_extension_names():
            xkeydefs = pemConf.GetExtensionBindings(extensionName)
            if xkeydefs:
                self.apply_bindings(xkeydefs)

        menuEventDict = {}
        for menu in self.mainmenu.menudefs:
            menuEventDict[menu[0]] = {}
            for item in menu[1]:
                if item:
                    menuEventDict[menu[0]][prepstr(item[0])[1]] = item[1]
        for menubarItem in self.menudict:
            menu = self.menudict[menubarItem]
            end = menu.index(END)
            if end is None:
                continue
            end += 1
            for index in range(0, end):
                if menu.type(index) == 'command':
                    accel = menu.entrycget(index, 'accelerator')
                    if accel:
                        itemName = menu.entrycget(index, 'label')
                        event = ''
                        if menubarItem in menuEventDict:
                            if itemName in menuEventDict[menubarItem]:
                                event = menuEventDict[menubarItem][itemName]
                        if event:
                            accel = get_accelerator(keydefs, event)
                            menu.entryconfig(index, accelerator=accel)

    def set_notabs_indentwidth(self):
        if not self.usetabs:
            self.indentwidth = pemConf.GetOption('main', 'Indent','num-spaces',
                                                  type='int')

    def reset_help_menu_entries(self):
        help_list = pemConf.GetAllExtraHelpSourcesList()
        helpmenu = self.menudict['help']
        helpmenu_length = helpmenu.index(END)
        if helpmenu_length > self.base_helpmenu_length:
            helpmenu.delete((self.base_helpmenu_length + 1), helpmenu_length)
        if help_list:
            helpmenu.add_separator()
            for entry in help_list:
                cmd = self._extra_help_callback(entry[1])
                helpmenu.add_command(label=entry[0], command=cmd)
        self.menudict['help'] = helpmenu

    def _extra_help_callback(self, resource):
        def display_extra_help(helpfile=resource):
            if not helpfile.startswith(('www', 'http')):
                helpfile = os.path.normpath(helpfile)
            if sys.platform[:3] == 'win':
                try:
                    os.startfile(helpfile)
                except OSError as why:
                    messagebox.showerror(title='Document Start Failure',
                        message=str(why), parent=self.text)
            else:
                webbrowser.open(helpfile)
        return display_extra_help

    def update_recent_files_list(self, new_file=None):
        rf_list = []
        file_path = self.recent_files_path
        if file_path and os.path.exists(file_path):
            with open(file_path,
                      encoding='utf_8', errors='replace') as rf_list_file:
                rf_list = rf_list_file.readlines()
        if new_file:
            new_file = os.path.abspath(new_file) + '\n'
            if new_file in rf_list:
                rf_list.remove(new_file)  
            rf_list.insert(0, new_file)
        bad_paths = []
        for path in rf_list:
            if '\0' in path or not os.path.exists(path[0:-1]):
                bad_paths.append(path)
        rf_list = [path for path in rf_list if path not in bad_paths]
        ulchars = "1234567890ABCDEFGHIJK"
        rf_list = rf_list[0:len(ulchars)]
        if file_path:
            try:
                with open(file_path, 'w',
                          encoding='utf_8', errors='replace') as rf_file:
                    rf_file.writelines(rf_list)
            except OSError as err:
                if not getattr(self.root, "recentfiles_message", False):
                    self.root.recentfiles_message = True
                    messagebox.showwarning(title='PEM Warning',
                        message="Cannot save Recent Files list to disk.\n"
                                f"  {err}\n"
                                "Select OK to continue.",
                        parent=self.text)
        for instance in self.top.instance_dict:
            menu = instance.recent_files_menu
            menu.delete(0, END)  
            for i, file_name in enumerate(rf_list):
                file_name = file_name.rstrip()  
                callback = instance.__recent_file_callback(file_name)
                menu.add_command(label=ulchars[i] + " " + file_name,
                                 command=callback,
                                 underline=0)

    def __recent_file_callback(self, file_name):
        def open_recent_file(fn_closure=file_name):
            self.io.open(editFile=fn_closure)
        return open_recent_file

    def saved_change_hook(self):
        short = self.short_title()
        long = self.long_title()
        if short and long and not macosx.isCocoaTk():
            title = short + " - " + long + _py_version
        elif short:
            title = short
        elif long:
            title = long
        else:
            title = "untitled"
        icon = short or long or title
        if not self.get_saved():
            title = "*%s*" % title
            icon = "*%s" % icon

        # --- TABBED GUI TITLE INTEGRATION ---
        if hasattr(self, 'main_container') and self.flist and hasattr(self.flist, 'notebook') and self.flist.notebook:
            try:
                # Tabs show only the short filename; the window title bar keeps the full detail
                tab_label = short or "untitled"
                if not self.get_saved():
                    tab_label = "*%s*" % tab_label
                tab_title = f"{tab_label}   ✕"
                self.flist.notebook.tab(self.main_container, text=tab_title)
                self.top.wm_title(f"PEM - {title}")
            except Exception:
                pass
        else:
            self.top.wm_title(title)
            self.top.wm_iconname(icon)

        if macosx.isCocoaTk():
            self.top.wm_attributes("-titlepath", long)
            self.top.wm_attributes("-modified", not self.get_saved())

    def get_saved(self):
        return self.undo.get_saved()

    def set_saved(self, flag):
        self.undo.set_saved(flag)

    def reset_undo(self):
        self.undo.reset_undo()

    def short_title(self):
        filename = self.io.filename
        # Return the numbered untitled name instead of a hardcoded string
        return os.path.basename(filename) if filename else getattr(self, 'untitled_name', "untitled")

    def long_title(self):
        return self.io.filename or ""

    def center_insert_event(self, event):
        self.center()
        return "break"

    def center(self, mark="insert"):
        text = self.text
        top, bot = self.getwindowlines()
        lineno = self.getlineno(mark)
        height = bot - top
        newtop = max(1, lineno - height//2)
        text.yview(float(newtop))

    def getwindowlines(self):
        text = self.text
        top = self.getlineno("@0,0")
        bot = self.getlineno("@0,65535")
        if top == bot and text.winfo_height() == 1:
            height = int(text['height'])
            bot = top + height - 1
        return top, bot

    def getlineno(self, mark="insert"):
        text = self.text
        return int(float(text.index(mark)))


    def _save_sash_position(self, event=None):
        try:
            if event is not None and event.widget is not self.paned_window:
                return
            if not hasattr(self, 'paned_window') or not self.paned_window.winfo_exists():
                return
            sash_pos = self.paned_window.sashpos(0)

            #print(f"[sash-save] release event, pos={sash_pos}")    # debug

            if sash_pos > 10:
                configSection = 'PyShell' if getattr(self, 'is_shell', False) else 'EditorWindow'
                pemConf.SetOption('main', configSection, 'sash-position', str(sash_pos))

                #print(f"[sash-save] wrote section={configSection} value={sash_pos}")   # debug

                # Read it right back to verify the in-memory store
                verify = pemConf.GetOption('main', configSection, 'sash-position',
                                              type='int', default=None, warn_on_default=False)
                #print(f"[sash-save] readback={verify}")    # debug

        except Exception as e:
            print(f"[sash-save] EXCEPTION: {e!r}")



    def get_geometry(self):
        geom = self.top.wm_geometry()

    def get_geometry(self):
        geom = self.top.wm_geometry()
        m = re.match(r"(\d+)x(\d+)\+(-?\d+)\+(-?\d+)", geom)
        return list(map(int, m.groups()))

    def restoreWindowGeometry(self):
        try:
            configSection = 'PyShell' if getattr(self, 'is_shell', False) else 'EditorWindow'

            # --- 1. WINDOW GEOMETRY ---
            # Only resize the main application window if it is the standalone Console, 
            # OR if this is the very first tab being created in the Notebook.
            is_first_tab_or_shell = self.is_shell or not (self.flist and hasattr(self.flist, 'notebook') and self.flist.notebook) or len(self.flist.notebook.tabs()) <= 1
            
            if is_first_tab_or_shell:
                savedWidth = pemConf.GetOption('main', configSection, 'window-width-pixels', type='int', default=None, warn_on_default=False)
                savedHeight = pemConf.GetOption('main', configSection, 'window-height-pixels', type='int', default=None, warn_on_default=False)
                savedX = pemConf.GetOption('main', configSection, 'window-x', type='int', default=None, warn_on_default=False)
                savedY = pemConf.GetOption('main', configSection, 'window-y', type='int', default=None, warn_on_default=False)

                if savedWidth and savedHeight and savedWidth >= 400 and savedHeight >= 300:
                    screenWidth = self.top.winfo_screenwidth()
                    screenHeight = self.top.winfo_screenheight()

                    maxWidth = int(screenWidth * 0.9)
                    maxHeight = int(screenHeight * 0.9)

                    finalWidth = min(savedWidth, maxWidth)
                    finalHeight = min(savedHeight, maxHeight)

                    if savedX is not None and savedY is not None:
                        finalX = max(0, min(savedX, screenWidth - 100))
                        finalY = max(0, min(savedY, screenHeight - 100))
                        geom_str = f"{finalWidth}x{finalHeight}+{finalX}+{finalY}"
                    else:
                        geom_str = f"{finalWidth}x{finalHeight}"

                    # Defer until after Tk's initial layout pass, otherwise the master
                    # window's "natural size" calculation can clobber our explicit geometry.
                    self.top.after_idle(lambda g=geom_str: self.top.winfo_exists() and self.top.geometry(g))

        except (TclError, ValueError, AttributeError):
            pass

    def close_event(self, event):
        self.close()
        return "break"

    def maybesave(self):
        if self.io:
            if not self.get_saved():
                if self.top.state()!='normal':
                    self.top.deiconify()
                self.top.lower()
                self.top.lift()
            return self.io.maybesave()

    def _is_last_editor_tab(self):
        """True if this editor is the only remaining tab in the editor window."""
        notebook = getattr(self.flist, 'notebook', None) if self.flist else None
        if notebook is None:
            return False
        try:
            return len(notebook.tabs()) <= 1
        except Exception:
            return False

    def close(self):
        # The editor window is PEM's canonical window: closing its last tab
        # exits PEM (which also shuts down the always-open Console). Other
        # closes -- a non-last tab, or any tab while PEM is already exiting --
        # just close that one tab.
        if (self.flist and not getattr(self, 'is_shell', False)
                and not getattr(self.flist, '_exiting', False)
                and self._is_last_editor_tab()):
            return self.flist.close_all_callback()
        try:
            reply = self.maybesave()
            if str(reply) != "cancel":
                self._close()
            return reply
        except AttributeError:
            pass

    def save_all_windows_event(self, event=None):
        if self.flist:
            for edit in list(self.flist.inversedict):
                if hasattr(edit, 'io') and edit.io and not edit.get_saved():
                    edit.text.event_generate("<<save-window>>")
        return "break"

    def quit_event(self, event=None):
        if self.flist:
            self.flist.close_all_callback()
        return "break"


    def _close(self):
        try:
            configSection = 'PyShell' if getattr(self, 'is_shell', False) else 'EditorWindow'

            # Capture geometry only if this window is actually visible/sized.
            # A withdrawn shell would return junk from wm_geometry().
            if self.top.state() == 'normal':
                width, height, x, y = self.get_geometry()
                
                pemConf.SetOption('main', configSection, 'window-width-pixels', str(width))
                pemConf.SetOption('main', configSection, 'window-height-pixels', str(height))
                pemConf.SetOption('main', configSection, 'window-x', str(x))
                pemConf.SetOption('main', configSection, 'window-y', str(y))

            # Always flush in-memory config to disk on the last instance,
            # regardless of whether THIS instance's window was visible.
            # The editor's geometry, the sash position, etc. were already
            # written to in-memory config earlier — they just need to survive.
            if len(self.top.instance_dict) <= 1:
                
                pemConf.userCfg['main'].Save()

        except (TclError, AttributeError):
            pass

        if self.io.filename:
            self.update_recent_files_list(new_file=self.io.filename)

        window.unregister_callback(self.postwindowsmenu)
        self.unload_extensions()
        self.io.close()
        self.io = None
        self.undo = None

        if self.color:
            self.color.close()
            self.color = None

        self.text = None
        self.tkinter_vars = None
        self.per.close()
        self.per = None

        if self.flist and hasattr(self.flist, 'notebook') and self.flist.notebook and not getattr(self, 'is_shell', False):
            # Capture strong references before self.close_hook() nullifies them!
            saved_flist = self.flist 
            saved_top = self.top
            try:
                saved_flist.notebook.forget(self.main_container)
                self.main_container.destroy()
                
                # -------------------------------------------------------------
                # LAST TAB CLOSED
                # Reached only while PEM is exiting (closing the last editor tab
                # routes through close_all_callback). Tear down the now-empty
                # editor window rather than leaving a blank notebook behind.
                # -------------------------------------------------------------
                if len(saved_flist.notebook.tabs()) == 0:
                    if saved_top.winfo_exists():
                        saved_top.destroy()
                    saved_flist.master_window = None
                    saved_flist.notebook = None
                    saved_flist.untitled_count = 0

            except Exception:
                pass
        else:
            self.top.destroy()

        if self.close_hook:
            self.close_hook()


    def load_extensions(self):
        self.extensions = {}
        self.load_standard_extensions()

    def unload_extensions(self):
        for ins in list(self.extensions.values()):
            if hasattr(ins, "close"):
                ins.close()
        self.extensions = {}

    def load_standard_extensions(self):
        for name in self.get_standard_extension_names():
            try:
                self.load_extension(name)
            except Exception:
                print("Failed to load extension", repr(name))
                traceback.print_exc()

    def get_standard_extension_names(self):
        return pemConf.GetExtensions(editor_only=True)

    extfiles = {}

    def load_extension(self, name):
        fname = self.extfiles.get(name, name)
        try:
            try:
                mod = importlib.import_module('.' + fname, package=__package__)
            except (ImportError, TypeError):
                mod = importlib.import_module(fname)
        except ImportError:
            print("\nFailed to import extension: ", name)
            raise
        cls = getattr(mod, name)
        keydefs = pemConf.GetExtensionBindings(name)
        if hasattr(cls, "menudefs"):
            self.fill_menus(cls.menudefs, keydefs)
        ins = cls(self)
        self.extensions[name] = ins
        if keydefs:
            self.apply_bindings(keydefs)
            for vevent in keydefs:
                methodname = vevent.replace("-", "_")
                while methodname[:1] == '<':
                    methodname = methodname[1:]
                while methodname[-1:] == '>':
                    methodname = methodname[:-1]
                methodname = methodname + "_event"
                if hasattr(ins, methodname):
                    self.text.bind(vevent, getattr(ins, methodname))

    def apply_bindings(self, keydefs=None):
        if keydefs is None:
            keydefs = self.mainmenu.default_keydefs
        text = self.text
        text.keydefs = keydefs
        for event, keylist in keydefs.items():
            if keylist:
                text.event_add(event, *keylist)

    def fill_menus(self, menudefs=None, keydefs=None):
        if menudefs is None:
            menudefs = self.mainmenu.menudefs
        if keydefs is None:
            keydefs = self.mainmenu.default_keydefs
        menudict = self.menudict
        text = self.text
        for mname, entrylist in menudefs:
            menu = menudict.get(mname)
            if not menu:
                continue
            for entry in entrylist:
                if entry is None:
                    menu.add_separator()
                else:
                    label, eventname = entry
                    checkbutton = (label[:1] == '!')
                    if checkbutton:
                        label = label[1:]
                    underline, label = prepstr(label)
                    accelerator = get_accelerator(keydefs, eventname)
                    def command(text=text, eventname=eventname):
                        text.event_generate(eventname)
                    if checkbutton:
                        var = self.get_var_obj(eventname, BooleanVar)
                        menu.add_checkbutton(label=label, underline=underline,
                            command=command, accelerator=accelerator,
                            variable=var)
                    else:
                        menu.add_command(label=label, underline=underline,
                                         command=command,
                                         accelerator=accelerator)

    def getvar(self, name):
        var = self.get_var_obj(name)
        if var:
            value = var.get()
            return value
        else:
            raise NameError(name)

    def setvar(self, name, value, vartype=None):
        var = self.get_var_obj(name, vartype)
        if var:
            var.set(value)
        else:
            raise NameError(name)

    def get_var_obj(self, eventname, vartype=None):
        var = self.tkinter_vars.get(eventname)
        if not var and vartype:
            self.tkinter_vars[eventname] = var = vartype(self.text)
        return var

    def is_char_in_string(self, text_index):
        if self.color:
            return self.text.tag_prevrange("TODO", text_index) or \
                   "STRING" in self.text.tag_names(text_index)
        else:
            return 1

    def get_selection_indices(self):
        try:
            first = self.text.index("sel.first")
            last = self.text.index("sel.last")
            return first, last
        except TclError:
            return None, None

    def get_tk_tabwidth(self):
        current = self.text['tabs'] or TK_TABWIDTH_DEFAULT
        return int(current)

    def set_tk_tabwidth(self, newtabwidth):
        text = self.text
        if self.get_tk_tabwidth() != newtabwidth:
            pixels = text.tk.call("font", "measure", text["font"],
                                  "-displayof", text.master,
                                  "n" * newtabwidth)
            text.configure(tabs=pixels)

    def set_indentation_params(self, is_py_src, guess=True):
        if is_py_src and guess:
            i = self.guess_indent()
            if 2 <= i <= 8:
                self.indentwidth = i
            if self.indentwidth != self.tabwidth:
                self.usetabs = False
        self.set_tk_tabwidth(self.tabwidth)

    def smart_backspace_event(self, event):
        text = self.text
        first, last = self.get_selection_indices()
        if first and last:
            text.delete(first, last)
            text.mark_set("insert", first)
            return "break"
        chars = text.get("insert linestart", "insert")
        if chars == '':
            if text.compare("insert", ">", "1.0"):
                text.delete("insert-1c")
            else:
                text.bell()     
            return "break"
        if  chars[-1] not in " \t":
            text.delete("insert-1c")
            return "break"
        tabwidth = self.tabwidth
        have = len(chars.expandtabs(tabwidth))
        assert have > 0
        want = ((have - 1) // self.indentwidth) * self.indentwidth
        ncharsdeleted = 0
        while True:
            chars = chars[:-1]
            ncharsdeleted = ncharsdeleted + 1
            have = len(chars.expandtabs(tabwidth))
            if have <= want or chars[-1] not in " \t":
                break
        text.undo_block_start()
        text.delete("insert-%dc" % ncharsdeleted, "insert")
        if have < want:
            text.insert("insert", ' ' * (want - have),
                        self.user_input_insert_tags)
        text.undo_block_stop()
        return "break"

    def smart_indent_event(self, event):
        text = self.text
        first, last = self.get_selection_indices()
        text.undo_block_start()
        try:
            if first and last:
                if index2line(first) != index2line(last):
                    return self.fregion.indent_region_event(event)
                text.delete(first, last)
                text.mark_set("insert", first)
            prefix = text.get("insert linestart", "insert")
            raw, effective = get_line_indent(prefix, self.tabwidth)
            if raw == len(prefix):
                self.reindent_to(effective + self.indentwidth)
            else:
                if self.usetabs:
                    pad = '\t'
                else:
                    effective = len(prefix.expandtabs(self.tabwidth))
                    n = self.indentwidth
                    pad = ' ' * (n - effective % n)
                text.insert("insert", pad, self.user_input_insert_tags)
            text.see("insert")
            return "break"
        finally:
            text.undo_block_stop()

    def newline_and_indent_event(self, event):
        text = self.text
        first, last = self.get_selection_indices()
        text.undo_block_start()
        try:  
            if first and last:
                text.delete(first, last)
                text.mark_set("insert", first)
            line = text.get("insert linestart", "insert")

            i, n = 0, len(line)
            while i < n and line[i] in " \t":
                i += 1
            if i == n:
                text.insert("insert linestart", '\n',
                            self.user_input_insert_tags)
                return "break"
            indent = line[:i]

            i = 0
            while line and line[-1] in " \t":
                line = line[:-1]
                i += 1
            if i:
                text.delete("insert - %d chars" % i, "insert")

            while text.get("insert") in " \t":
                text.delete("insert")

            text.insert("insert", '\n', self.user_input_insert_tags)

            lno = index2line(text.index('insert'))
            y = pyparse.Parser(self.indentwidth, self.tabwidth)
            if not self.prompt_last_line:
                for context in self.num_context_lines:
                    startat = max(lno - context, 1)
                    startatindex = repr(startat) + ".0"
                    rawtext = text.get(startatindex, "insert")
                    y.set_code(rawtext)
                    bod = y.find_good_parse_start(
                            self._build_char_in_string_func(startatindex))
                    if bod is not None or startat == 1:
                        break
                y.set_lo(bod or 0)
            else:
                r = text.tag_prevrange("console", "insert")
                if r:
                    startatindex = r[1]
                else:
                    startatindex = "1.0"
                rawtext = text.get(startatindex, "insert")
                y.set_code(rawtext)
                y.set_lo(0)

            c = y.get_continuation_type()
            if c != pyparse.C_NONE:
                if c == pyparse.C_STRING_FIRST_LINE:
                    pass
                elif c == pyparse.C_STRING_NEXT_LINES:
                    text.insert("insert", indent, self.user_input_insert_tags)
                elif c == pyparse.C_BRACKET:
                    self.reindent_to(y.compute_bracket_indent())
                elif c == pyparse.C_BACKSLASH:
                    if y.get_num_lines_in_stmt() > 1:
                        text.insert("insert", indent,
                                    self.user_input_insert_tags)
                    else:
                        self.reindent_to(y.compute_backslash_indent())
                else:
                    assert 0, f"bogus continuation type {c!r}"
                return "break"

            indent = y.get_base_indent_string()
            text.insert("insert", indent, self.user_input_insert_tags)
            if y.is_block_opener():
                self.smart_indent_event(event)
            elif indent and y.is_block_closer():
                self.smart_backspace_event(event)
            return "break"
        finally:
            text.see("insert")
            text.undo_block_stop()

    def _build_char_in_string_func(self, startindex):
        def inner(offset, _startindex=startindex,
                  _icis=self.is_char_in_string):
            return _icis(_startindex + "+%dc" % offset)
        return inner

    def _make_blanks(self, n):
        if self.usetabs:
            ntabs, nspaces = divmod(n, self.tabwidth)
            return '\t' * ntabs + ' ' * nspaces
        else:
            return ' ' * n

    def reindent_to(self, column):
        text = self.text
        text.undo_block_start()
        if text.compare("insert linestart", "!=", "insert"):
            text.delete("insert linestart", "insert")
        if column:
            text.insert("insert", self._make_blanks(column),
                        self.user_input_insert_tags)
        text.undo_block_stop()

    def guess_indent(self):
        opener, indented = IndentSearcher(self.text).run()
        if opener and indented:
            raw, indentsmall = get_line_indent(opener, self.tabwidth)
            raw, indentlarge = get_line_indent(indented, self.tabwidth)
        else:
            indentsmall = indentlarge = 0
        return indentlarge - indentsmall

    def toggle_line_numbers_event(self, event=None):
        if self.line_numbers is None:
            return

        if self.line_numbers.is_shown:
            self.line_numbers.hide_sidebar()
            menu_label = "Show"
        else:
            self.line_numbers.show_sidebar()
            menu_label = "Hide"
        self.update_menu_label(menu='options', index='*ine*umbers',
                               label=f'{menu_label} Line Numbers')

    # -------------------------------------------------------------------------
    # INTEGRATED IO REDIRECTION API
    # -------------------------------------------------------------------------
    def write_output(self, text_content, is_error=False):
        """Append a chunk of script output to the tab's bottom output pane."""
        if not getattr(self, 'output_text', None):
            return
        if not self.output_text.winfo_exists():
            return
        # perflog: count output writes per run so a flood (a program spamming
        # stdout, an error loop, etc.) shows up in a PEM_PERF trace.
        n = getattr(self, '_perf_output_count', 0) + 1
        self._perf_output_count = n
        if n == 1 or n == 100 or n == 1000 or (n >= 5000 and n % 5000 == 0):
            from pem import perflog
            perflog.mark(f"editor.write_output: {n} write(s) this run")

        # Direct path: insert immediately, like the console does.
        # Treat embedded \r terminal-style: each segment after a \r overwrites
        # the current trailing line, so tqdm-style progress bars collapse to
        # one updating line instead of stacking up as thousands of lines.
        tag = "error" if is_error else ""
        self.output_text.config(state='normal')
        text_content = text_content.replace('\r\n', '\n')
        parts = text_content.split('\r')
        self.output_text.insert("end", parts[0], tag)
        for part in parts[1:]:
            self.output_text.delete("end-1c linestart", "end-1c")
            self.output_text.insert("end", part, tag)
        self.output_text.config(state='disabled')

        # Schedule a single autoscroll on the next idle tick. Cancel any
        # prior pending one so rapid prints collapse into one scroll.
        if getattr(self, '_output_autoscroll_id', None):
            try:
                self.output_text.after_cancel(self._output_autoscroll_id)
            except Exception:
                pass
        self._output_autoscroll_id = self.output_text.after_idle(
            self._autoscroll_output)

        # Periodically trim if we're accumulating a lot of output.
        self._output_lines_since_trim = getattr(
            self, '_output_lines_since_trim', 0) + 1
        if self._output_lines_since_trim > 1000:
            self._output_lines_since_trim = 0
            self._maybe_trim_output()


    def _autoscroll_output(self):
        self._output_autoscroll_id = None
        try:
            if self.output_text.winfo_exists():
                self.output_text.see("end")
        except Exception:
            pass


    def _maybe_trim_output(self):
        """Trim the output pane if it exceeds the line cap."""
        if not self.output_text.winfo_exists():
            return
        OUTPUT_MAX_LINES  = 20000
        OUTPUT_KEEP_LINES = 10000
        total_lines = int(self.output_text.index('end-1c').split('.')[0])
        if total_lines > OUTPUT_MAX_LINES:
            self.output_text.config(state='normal')
            cutoff = total_lines - OUTPUT_KEEP_LINES
            self.output_text.delete('1.0', f'{cutoff}.0')
            self.output_text.insert('1.0',
                f"[... {cutoff - 1} earlier lines trimmed ...]\n")
            self.output_text.config(state='disabled')


    def clear_output(self):
        """Purge the output pane prior to execution."""
        self._perf_output_count = 0
        if not getattr(self, 'output_text', None):
            return
        # Cancel any pending autoscroll.
        if getattr(self, '_output_autoscroll_id', None):
            try:
                self.output_text.after_cancel(self._output_autoscroll_id)
            except Exception:
                pass
            self._output_autoscroll_id = None
        self._output_lines_since_trim = 0
        self.output_text.config(state='normal')
        self.output_text.delete('1.0', "end")
        self.output_text.config(state='disabled')


def index2line(index):
    return int(float(index))


_line_indent_re = re.compile(r'[ \t]*')
def get_line_indent(line, tabwidth):
    m = _line_indent_re.match(line)
    return m.end(), len(m.group().expandtabs(tabwidth))


class IndentSearcher:
    "Tokenizes a buffer to guess its indent width (first indented line after a block opener)."

    def __init__(self, text):
        self.text = text
        self.i = self.finished = 0
        self.blkopenline = self.indentedline = None

    def readline(self):
        if self.finished:
            return ""
        i = self.i = self.i + 1
        mark = repr(i) + ".0"
        if self.text.compare(mark, ">=", "end"):
            return ""
        return self.text.get(mark, mark + " lineend+1c")

    def tokeneater(self, type, token, start, end, line,
                   INDENT=tokenize.INDENT,
                   NAME=tokenize.NAME,
                   OPENERS=('class', 'def', 'for', 'if', 'match', 'try',
                            'while', 'with')):
        if self.finished:
            pass
        elif type == NAME and token in OPENERS:
            self.blkopenline = line
        elif type == INDENT and self.blkopenline:
            self.indentedline = line
            self.finished = 1

    def run(self):
        try:
            tokens = tokenize.generate_tokens(self.readline)
            for token in tokens:
                self.tokeneater(*token)
        except (tokenize.TokenError, SyntaxError):
            pass
        return self.blkopenline, self.indentedline


def prepstr(s):
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


def fixwordbreaks(root):
    tk = root.tk
    tk.call('tcl_wordBreakAfter', 'a b', 0) 
    tk.call('set', 'tcl_wordchars', r'\w')
    tk.call('set', 'tcl_nonwordchars', r'\W')


def _editor_window(parent):  
    root = parent
    fixwordbreaks(root)
    if sys.argv[1:]:
        filename = sys.argv[1]
    else:
        filename = None
    macosx.setupApp(root, None)
    edit = EditorWindow(root=root, filename=filename)
    text = edit.text
    text['height'] = 10
    for i in range(20):
        text.insert('insert', '  '*i + str(i) + '\n')


if __name__ == '__main__':
    from unittest import main
    main('pem.pem_test.test_editor', verbosity=2, exit=False)

    from pem.pem_test.htest import run
    run(_editor_window)