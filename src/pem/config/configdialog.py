"""PEM Configuration Dialog: support user customization of PEM by GUI

Customize font faces, sizes, and colorization attributes.  Set indentation
defaults.  Customize keybindings.  Colorization and keybindings can be
saved as user defined sets.  Select startup options including shell/editor
and default window size.  Define additional help sources.

Note that tab width in PEM is currently fixed at eight due to Tk issues.
Refer to comments in EditorWindow autoindent code for details.

"""
import re

from tkinter import (Toplevel, Listbox, Canvas,
                     StringVar, BooleanVar, IntVar, TRUE, FALSE,
                     TOP, BOTTOM, RIGHT, LEFT, SOLID, GROOVE,
                     NONE, BOTH, X, Y, W, E, EW, NS, NSEW, NW,
                     HORIZONTAL, VERTICAL, ANCHOR, ACTIVE, END, TclError)
from tkinter.ttk import (Frame, LabelFrame, Button, Checkbutton, Entry, Label,
                         OptionMenu, Notebook, Radiobutton, Scrollbar, Style,
                         Spinbox, Combobox)
from tkinter import colorchooser
import tkinter.font as tkfont
from tkinter import messagebox

from pem.config import pemConf, ConfigChanges
from pem.config.config_key import GetKeysWindow
from pem.dialogs.dynoption import DynOptionMenu
from pem import macosx
from pem.dialogs.query import SectionName, HelpSource
from pem.dialogs.textview import view_text
from pem.editing.codecontext import CodeContext
from pem.text.parenmatch import ParenMatch
from pem.text.format import FormatParagraph
from pem.shell.squeezer import Squeezer
from pem.dialogs.textview import ScrollableTextFrame

changes = ConfigChanges()
# Reload changed options in the following classes.
reloadables = (CodeContext, ParenMatch, FormatParagraph,
               Squeezer)


class ConfigDialog(Toplevel):
    """Config dialog for PEM.
    """

    def __init__(self, parent, title='', *, _htest=False, _utest=False):
        """Show the tabbed dialog for user configuration.

        Args:
            parent - parent of this dialog
            title - string which is the title of this popup dialog
            _htest - bool, change box location when running htest
            _utest - bool, don't wait_window when running unittest

        Note: Focus set on font page fontlist.

        Methods:
            create_widgets
            cancel: Bound to DELETE_WINDOW protocol.
        """
        Toplevel.__init__(self, parent)
        self.parent = parent
        if _htest:
            parent.instance_dict = {}
        if not _utest:
            self.withdraw()

        self.title(title or 'PEM Preferences')
        x = parent.winfo_rootx() + 20
        y = parent.winfo_rooty() + (30 if not _htest else 150)
        self.geometry(f'+{x}+{y}')
        # Each theme element key is its display name.
        # The first value of the tuple is the sample area tag name.
        # The second value is the display name list sort index.
        self.create_widgets()
        self.resizable(height=FALSE, width=FALSE)
        self.transient(parent)
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        # self.fontpage.fontlist.focus_set()  # *** PEM Edit
        # XXX Decide whether to keep or delete these key bindings.
        # Key bindings for this dialog.
        # self.bind('<Escape>', self.Cancel) #dismiss dialog, no save
        # self.bind('<Alt-a>', self.Apply) #apply changes, save
        # self.bind('<F1>', self.Help) #context help
        # Attach callbacks after loading config to avoid calling them.
        tracers.attach()

        if not _utest:
            self.grab_set()
            self.wm_deiconify()
            self.wait_window()


    def create_widgets(self):
        """Create and place widgets for tabbed dialog.

        Widgets Bound to self:
            frame: encloses all other widgets
            note: Notebook
            highpage: HighPage
            genpage: GeneralPage

        Methods:
            create_action_buttons
            load_configs: Load pages except for extensions.
            activate_config_changes: Tell editors to reload.
        """
        # -----------------------------------------------------------------
        # SUBSYSTEM: DIALOG STYLING ENGINE
        # -----------------------------------------------------------------
        import sys
        style = Style(self)
        
        # Only force the custom flat 'clam' theme on Windows and Linux.
        # On macOS, preserve the native Apple 'aqua' theme for rounded, native controls!
        if sys.platform != 'darwin':
            if 'clam' in style.theme_names():
                style.theme_use('clam')
            # Force the dialog backgrounds to match the flat IDE aesthetic on Windows/Linux
            self.configure(bg='#e0e0e0')
            style.configure('.', background='#e0e0e0')
        # -----------------------------------------------------------------

        self.frame = Frame(self, padding=5)
        self.frame.grid(sticky="nwes")
        self.note = note = Notebook(self.frame)

        self.genpage = GeneralPage(note)
        # *** PEM Edit: Removed Fonts, Keys, Windows, Console/Editor, and Extensions tabs.
        # These are still instantiated below if needed by other pages but not added to the notebook.
        self.extpage = ExtPage(note)
        self.highpage = HighPage(note, self.extpage)

        note.add(self.genpage, text=' General ')
        note.add(self.highpage, text=' Style ')
        note.enable_traversal()
        note.pack(side=TOP, expand=TRUE, fill=BOTH)
        self.create_action_buttons().pack(side=BOTTOM)

    def create_action_buttons(self):
        """Return frame of action buttons for dialog.

        Methods:
            ok
            apply
            cancel
            help

        Widget Structure:
            outer: Frame
                buttons: Frame
                    (no assignment): Button (ok)
                    (no assignment): Button (apply)
                    (no assignment): Button (cancel)
                    (no assignment): Button (help)
                (no assignment): Frame
        """
        if macosx.isAquaTk():
            # Changing the default padding on OSX results in unreadable
            # text in the buttons.
            padding_args = {}
        else:
            padding_args = {'padding': (6, 3)}
        outer = Frame(self.frame, padding=2)
        buttons_frame = Frame(outer, padding=2)
        self.buttons = {}
        for txt, cmd in (
            ('Ok', self.ok),
            ('Apply', self.apply),
            ('Cancel', self.cancel)):
            self.buttons[txt] = Button(buttons_frame, text=txt, command=cmd,
                       takefocus=FALSE, **padding_args)
            self.buttons[txt].pack(side=LEFT, padx=5)
        # Add space above buttons.
        Frame(outer, height=2, borderwidth=0).pack(side=TOP)
        buttons_frame.pack(side=BOTTOM)
        return outer

    def ok(self):
        """Apply config changes, then dismiss dialog."""
        self.apply()
        self.destroy()

    def apply(self):
        """Apply config changes and leave dialog open."""
        self.deactivate_current_config()
        changes.save_all()
        self.extpage.save_all_changed_extensions()
        self.activate_config_changes()

    def cancel(self):
        """Dismiss config dialog.

        Methods:
            destroy: inherited
        """
        changes.clear()
        self.destroy()

    def destroy(self):
        # *** PEM Edit: FontPage removed, no need to save font_sample_text
        # global font_sample_text
        # font_sample_text = self.fontpage.font_sample.get('1.0', 'end')
        self.grab_release()
        super().destroy()

    def help(self):
        """Create textview for config dialog help.

        Attributes accessed:
            note
        Methods:
            view_text: Method from textview module.
        """
        page = self.note.tab(self.note.select(), option='text').strip()
        view_text(self, title='Help for PEM preferences',
                  contents=help_common+help_pages.get(page, ''))

    def deactivate_current_config(self):
        """Remove current key bindings in current windows."""
        for instance in self.parent.instance_dict:
            instance.RemoveKeybindings()

    def activate_config_changes(self):
        """Apply configuration changes to current windows.

        Dynamically update the current parent window instances
        with some of the configuration changes.
        """
        for instance in self.parent.instance_dict:
            instance.ResetColorizer()
            instance.ResetFont()
            instance.set_notabs_indentwidth()
            instance.ApplyKeybindings()
            instance.reset_help_menu_entries()
            instance.update_cursor_blink()
            
            # Apply Code Context changes
            if hasattr(instance, 'code_context') and instance.code_context is not None:
                enabled = pemConf.GetOption('main', 'EditorWindow', 'code-context-default',
                                            type='bool', default=False)
                if (instance.code_context.context is not None) != enabled:
                    instance.code_context.toggle_code_context_event()

        for klass in reloadables:
            klass.reload()



# class TabPage(Frame):  # A template for Page classes.
#     def __init__(self, master):
#         super().__init__(master)
#         self.create_page_tab()
#         self.load_tab_cfg()
#     def create_page_tab(self):
#         # Define tk vars and register var and callback with tracers.
#         # Create subframes and widgets.
#         # Pack widgets.
#     def load_tab_cfg(self):
#         # Initialize widgets with data from pemConf.
#     def var_changed_var_name():
#         # For each tk var that needs other than default callback.
#     def other_methods():
#         # Define tab-specific behavior.

font_sample_text = (
    '<ASCII/Latin1>\n'
    'AaBbCcDdEeFfGgHhIiJj\n1234567890#:+=(){}[]\n'
    '\u00a2\u00a3\u00a5\u00a7\u00a9\u00ab\u00ae\u00b6\u00bd\u011e'
    '\u00c0\u00c1\u00c2\u00c3\u00c4\u00c5\u00c7\u00d0\u00d8\u00df\n'
    '\n<IPA,Greek,Cyrillic>\n'
    '\u0250\u0255\u0258\u025e\u025f\u0264\u026b\u026e\u0270\u0277'
    '\u027b\u0281\u0283\u0286\u028e\u029e\u02a2\u02ab\u02ad\u02af\n'
    '\u0391\u03b1\u0392\u03b2\u0393\u03b3\u0394\u03b4\u0395\u03b5'
    '\u0396\u03b6\u0397\u03b7\u0398\u03b8\u0399\u03b9\u039a\u03ba\n'
    '\u0411\u0431\u0414\u0434\u0416\u0436\u041f\u043f\u0424\u0444'
    '\u0427\u0447\u042a\u044a\u042d\u044d\u0460\u0464\u046c\u04dc\n'
    '\n<Hebrew, Arabic>\n'
    '\u05d0\u05d1\u05d2\u05d3\u05d4\u05d5\u05d6\u05d7\u05d8\u05d9'
    '\u05da\u05db\u05dc\u05dd\u05de\u05df\u05e0\u05e1\u05e2\u05e3\n'
    '\u0627\u0628\u062c\u062f\u0647\u0648\u0632\u062d\u0637\u064a'
    '\u0660\u0661\u0662\u0663\u0664\u0665\u0666\u0667\u0668\u0669\n'
    '\n<Devanagari, Tamil>\n'
    '\u0966\u0967\u0968\u0969\u096a\u096b\u096c\u096d\u096e\u096f'
    '\u0905\u0906\u0907\u0908\u0909\u090a\u090f\u0910\u0913\u0914\n'
    '\u0be6\u0be7\u0be8\u0be9\u0bea\u0beb\u0bec\u0bed\u0bee\u0bef'
    '\u0b85\u0b87\u0b89\u0b8e\n'
    '\n<East Asian>\n'
    '\u3007\u4e00\u4e8c\u4e09\u56db\u4e94\u516d\u4e03\u516b\u4e5d\n'
    '\u6c49\u5b57\u6f22\u5b57\u4eba\u6728\u706b\u571f\u91d1\u6c34\n'
    '\uac00\ub0d0\ub354\ub824\ubaa8\ubd64\uc218\uc720\uc988\uce58\n'
    '\u3042\u3044\u3046\u3048\u304a\u30a2\u30a4\u30a6\u30a8\u30aa\n'
    )


class GeneralPage(Frame):
    "Settings dialog tab: window size, autosave, help sources, and extensions."

    def __init__(self, master):
        super().__init__(master)
        self.create_page_general()
        self.load_general_cfg()

    def create_page_general(self):
        self.font_size = tracers.add(StringVar(self), ('main', 'EditorWindow', 'font-size'))
        self.font_bold = tracers.add(BooleanVar(self), ('main', 'EditorWindow', 'font-bold'))
        self.indent_spaces = tracers.add(StringVar(self), ('main', 'Indent', 'num-spaces'))
        self.auto_indent = tracers.add(BooleanVar(self), ('main', 'Indent', 'auto-indent'))
        self.highlight_current_line = tracers.add(BooleanVar(self), ('main', 'EditorWindow', 'highlight-current-line'))
        self.code_context_default = tracers.add(BooleanVar(self), ('main', 'EditorWindow', 'code-context-default'))
        self.autosave = tracers.add(BooleanVar(self), ('main', 'General', 'autosave'))
        self.exe_console = tracers.add(BooleanVar(self), ('main', 'CreateExecutable', 'console'))
        self.exe_quit_on_close = tracers.add(BooleanVar(self), ('main', 'CreateExecutable', 'quit-on-window-close'))

        # Create widgets
        frame = Frame(self, borderwidth=0)
        frame.pack(padx=20, pady=20, fill=BOTH, expand=TRUE)

        # Appearance Group
        frame_appearance = LabelFrame(frame, text=' Appearance ')
        frame_appearance.pack(fill=X, padx=5, pady=5)

        # 1. Font Size
        row1 = Frame(frame_appearance)
        row1.pack(fill=X, padx=8, pady=4)
        Label(row1, text="Font Size:").pack(side=LEFT)
        self.font_size_spin = Spinbox(row1, from_=8, to=40, width=5, textvariable=self.font_size)
        self.font_size_spin.pack(side=LEFT, padx=10)

        # 2. Bold Font
        self.font_bold_cb = Checkbutton(frame_appearance, text="Bold Font", variable=self.font_bold)
        self.font_bold_cb.pack(anchor=W, padx=8, pady=4)

        # 3. Indent Width
        row2 = Frame(frame_appearance)
        row2.pack(fill=X, padx=8, pady=4)
        Label(row2, text="Indent Width:").pack(side=LEFT)
        self.indent_spin = Spinbox(row2, from_=1, to=8, width=5, textvariable=self.indent_spaces)
        self.indent_spin.pack(side=LEFT, padx=10)

        # Behavior Group
        frame_behavior = LabelFrame(frame, text=' Behavior ')
        frame_behavior.pack(fill=X, padx=5, pady=5)

        # 3. Automatic Indent
        self.auto_indent_cb = Checkbutton(frame_behavior, text="Automatic Indent", variable=self.auto_indent)
        self.auto_indent_cb.pack(anchor=W, padx=8, pady=4)

        # 4. Highlight Current Line
        self.highlight_line_cb = Checkbutton(frame_behavior, text="Highlight Current Line", variable=self.highlight_current_line)
        self.highlight_line_cb.pack(anchor=W, padx=8, pady=4)

        # 5. Show Code Context
        self.code_context_cb = Checkbutton(frame_behavior, text="Show Code Context", variable=self.code_context_default)
        self.code_context_cb.pack(anchor=W, padx=8, pady=4)

        # File Group
        frame_file = LabelFrame(frame, text=' File ')
        frame_file.pack(fill=X, padx=5, pady=5)

        # 6. Auto Save Before Run
        self.autosave_cb = Checkbutton(frame_file, text="Auto Save Before Run", variable=self.autosave)
        self.autosave_cb.pack(anchor=W, padx=8, pady=4)

        # Create Executable Group
        frame_exe = LabelFrame(frame, text=' Create Executable ')
        frame_exe.pack(fill=X, padx=5, pady=5)

        # 7. Show Console -- when on, built programs open a terminal window so
        # they can use print() and input().  Off keeps them windowed.
        self.exe_console_cb = Checkbutton(frame_exe, text="Show Console", variable=self.exe_console)
        self.exe_console_cb.pack(anchor=W, padx=8, pady=(4, 0))
        Label(frame_exe,
              text="Give built programs a text console for print() and input().",
              foreground="gray40").pack(anchor=W, padx=28, pady=(0, 4))

        # 8. Quit When Last Window Closes -- when on, a built window program ends
        # once its last window closes.  Off by default: some features (e.g.
        # MidiIn's device chooser) open and close a window while the program runs.
        self.exe_quit_on_close_cb = Checkbutton(frame_exe, text="Quit When Last Window Closes",
                                                variable=self.exe_quit_on_close)
        self.exe_quit_on_close_cb.pack(anchor=W, padx=8, pady=(4, 0))
        Label(frame_exe,
              text="End a built window program when its last window is closed.",
              foreground="gray40").pack(anchor=W, padx=28, pady=(0, 4))

        # Restore Defaults button
        Button(frame, text="Restore Defaults", command=self.restore_defaults).pack(side=BOTTOM, pady=10)

    def load_general_cfg(self):
        self.font_size.set(pemConf.GetOption('main', 'EditorWindow', 'font-size', type='int', default=12))
        self.font_bold.set(pemConf.GetOption('main', 'EditorWindow', 'font-bold', type='bool', default=False))
        self.indent_spaces.set(pemConf.GetOption('main', 'Indent', 'num-spaces', type='int', default=3))
        self.auto_indent.set(pemConf.GetOption('main', 'Indent', 'auto-indent', type='bool', default=True))
        self.highlight_current_line.set(pemConf.GetOption('main', 'EditorWindow', 'highlight-current-line', type='bool', default=False))
        self.code_context_default.set(pemConf.GetOption('main', 'EditorWindow', 'code-context-default', type='bool', default=False))
        self.autosave.set(pemConf.GetOption('main', 'General', 'autosave', type='bool', default=False))
        self.exe_console.set(pemConf.GetOption('main', 'CreateExecutable', 'console', type='bool', default=False))
        self.exe_quit_on_close.set(pemConf.GetOption('main', 'CreateExecutable', 'quit-on-window-close', type='bool', default=True))

    def restore_defaults(self):
        """Reset all General tab settings to their default values."""
        self.font_size.set(12)
        self.font_bold.set(False)
        self.indent_spaces.set(3)
        self.auto_indent.set(True)
        self.highlight_current_line.set(False)
        self.code_context_default.set(False)
        self.autosave.set(False)
        self.exe_console.set(False)
        self.exe_quit_on_close.set(True)

        # # Implicitly apply changes
        # config_dialog = self.master.winfo_toplevel()
        # if hasattr(config_dialog, 'apply'):
        #     config_dialog.apply()


class FontPage(Frame):
    "Settings dialog tab: editor font face, size, and bold, with a live sample."

    def __init__(self, master, highpage):
        super().__init__(master)
        self.highlight_sample = highpage.highlight_sample
        self.create_page_font()
        self.load_font_cfg()

    def create_page_font(self):
        """Return frame of widgets for Font tab.

        Fonts: Enable users to provisionally change font face, size, or
        boldness and to see the consequence of proposed choices.  Each
        action set 3 options in changes structuree and changes the
        corresponding aspect of the font sample on this page and
        highlight sample on highlight page.

        Function load_font_cfg initializes font vars and widgets from
        pemConf entries and tk.

        Fontlist: mouse button 1 click or up or down key invoke
        on_fontlist_select(), which sets var font_name.

        Sizelist: clicking the menubutton opens the dropdown menu. A
        mouse button 1 click or return key sets var font_size.

        Bold_toggle: clicking the box toggles var font_bold.

        Changing any of the font vars invokes var_changed_font, which
        adds all 3 font options to changes and calls set_samples.
        Set_samples applies a new font constructed from the font vars to
        font_sample and to highlight_sample on the highlight page.

        Widgets for FontPage(Frame):  (*) widgets bound to self
            frame_font: LabelFrame
                frame_font_name: Frame
                    font_name_title: Label
                    (*)fontlist: ListBox - font_name
                    scroll_font: Scrollbar
                frame_font_param: Frame
                    font_size_title: Label
                    (*)sizelist: DynOptionMenu - font_size
                    (*)bold_toggle: Checkbutton - font_bold
            frame_sample: LabelFrame
                (*)font_sample: Label
        """
        self.font_name = tracers.add(StringVar(self), self.var_changed_font)
        self.font_size = tracers.add(StringVar(self), self.var_changed_font)
        self.font_bold = tracers.add(BooleanVar(self), self.var_changed_font)

        # Define frames and widgets.
        frame_font = LabelFrame(self, text=' Console/Editor Font ')
        frame_sample = LabelFrame(self, text=' Font Sample (Editable) ')
        # frame_font.
        frame_font_name = Frame(frame_font)
        frame_font_param = Frame(frame_font)
        font_name_title = Label(
                frame_font_name, justify=LEFT, text='Font Face :')
        self.fontlist = Listbox(frame_font_name, height=15,
                                takefocus=True, exportselection=FALSE)
        self.fontlist.bind('<ButtonRelease-1>', self.on_fontlist_select)
        self.fontlist.bind('<KeyRelease-Up>', self.on_fontlist_select)
        self.fontlist.bind('<KeyRelease-Down>', self.on_fontlist_select)
        scroll_font = Scrollbar(frame_font_name)
        scroll_font.config(command=self.fontlist.yview)
        self.fontlist.config(yscrollcommand=scroll_font.set)
        font_size_title = Label(frame_font_param, text='Size :')
        self.sizelist = DynOptionMenu(frame_font_param, self.font_size, None)
        self.bold_toggle = Checkbutton(
                frame_font_param, variable=self.font_bold,
                onvalue=1, offvalue=0, text='Bold')
        # frame_sample.
        font_sample_frame = ScrollableTextFrame(frame_sample)
        self.font_sample = font_sample_frame.text
        self.font_sample.config(wrap=NONE, width=1, height=1)
        self.font_sample.insert(END, font_sample_text)

        # Grid and pack widgets:
        self.columnconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)
        frame_font.grid(row=0, column=0, padx=5, pady=5)
        frame_sample.grid(row=0, column=1, rowspan=3, padx=5, pady=5,
                          sticky='nsew')
        # frame_font.
        frame_font_name.pack(side=TOP, padx=5, pady=5, fill=X)
        frame_font_param.pack(side=TOP, padx=5, pady=5, fill=X)
        font_name_title.pack(side=TOP, anchor=W)
        self.fontlist.pack(side=LEFT, expand=TRUE, fill=X)
        scroll_font.pack(side=LEFT, fill=Y)
        font_size_title.pack(side=LEFT, anchor=W)
        self.sizelist.pack(side=LEFT, anchor=W)
        self.bold_toggle.pack(side=LEFT, anchor=W, padx=20)
        # frame_sample.
        font_sample_frame.pack(expand=TRUE, fill=BOTH)

    def load_font_cfg(self):
        """Load current configuration settings for the font options.

        Retrieve current font with pemConf.GetFont and font families
        from tk. Setup fontlist and set font_name.  Setup sizelist,
        which sets font_size.  Set font_bold.  Call set_samples.
        """
        configured_font = pemConf.GetFont(self, 'main', 'EditorWindow')
        font_name = configured_font[0].lower()
        font_size = configured_font[1]
        font_bold  = configured_font[2]=='bold'

        # Set sorted no-duplicate editor font selection list and font_name.
        fonts = sorted(set(tkfont.families(self)))
        for font in fonts:
            self.fontlist.insert(END, font)
        self.font_name.set(font_name)
        lc_fonts = [s.lower() for s in fonts]
        try:
            current_font_index = lc_fonts.index(font_name)
            self.fontlist.see(current_font_index)
            self.fontlist.select_set(current_font_index)
            self.fontlist.select_anchor(current_font_index)
            self.fontlist.activate(current_font_index)
        except ValueError:
            pass
        # Set font size dropdown.
        self.sizelist.SetMenu(('7', '8', '9', '10', '11', '12', '13', '14',
                               '16', '18', '20', '22', '25', '29', '34', '40'),
                              font_size)
        # Set font weight.
        self.font_bold.set(font_bold)
        self.set_samples()

    def var_changed_font(self, *params):
        """Store changes to font attributes.

        When one font attribute changes, save them all, as they are
        not independent from each other. In particular, when we are
        overriding the default font, we need to write out everything.
        """
        value = self.font_name.get()
        changes.add_option('main', 'EditorWindow', 'font', value)
        value = self.font_size.get()
        changes.add_option('main', 'EditorWindow', 'font-size', value)
        value = self.font_bold.get()
        changes.add_option('main', 'EditorWindow', 'font-bold', value)
        self.set_samples()

    def on_fontlist_select(self, event):
        """Handle selecting a font from the list.

        Event can result from either mouse click or Up or Down key.
        Set font_name and example displays to selection.
        """
        font = self.fontlist.get(
                ACTIVE if event.type.name == 'KeyRelease' else ANCHOR)
        self.font_name.set(font.lower())

    def set_samples(self, event=None):
        """Update update both screen samples with the font settings.

        Called on font initialization and change events.
        Accesses font_name, font_size, and font_bold Variables.
        Updates font_sample and highlight page highlight_sample.
        """
        font_name = self.font_name.get()
        font_weight = tkfont.BOLD if self.font_bold.get() else tkfont.NORMAL
        new_font = (font_name, self.font_size.get(), font_weight)
        self.font_sample['font'] = new_font
        self.highlight_sample['font'] = new_font


class HighPage(Frame):
    "Settings dialog tab: syntax-highlighting themes -- pick, preview, and edit colours."

    def __init__(self, master, extpage):
        super().__init__(master)
        self.extpage = extpage
        self.cd = master.winfo_toplevel()
        self.style = Style(master)
        self.create_page_highlight()
        self.load_theme_cfg()

    def create_page_highlight(self):
        """Return frame of widgets for Highlights tab.

        Enable users to provisionally change foreground and background
        colors applied to textual tags.  Color mappings are stored in
        complete listings called themes.  Built-in themes in
        pem/config-highlight.def are fixed as far as the dialog is
        concerned. Any theme can be used as the base for a new custom
        theme, stored in .pemrc/config-highlight.cfg.

        Function load_theme_cfg() initializes tk variables and theme
        lists and calls paint_theme_sample() and set_highlight_target()
        for the current theme.  Radiobuttons builtin_theme_on and
        custom_theme_on toggle var theme_source, which controls if the
        current set of colors are from a builtin or custom theme.
        DynOptionMenus builtinlist and customlist contain lists of the
        builtin and custom themes, respectively, and the current item
        from each list is stored in vars builtin_name and custom_name.

        Function paint_theme_sample() applies the colors from the theme
        to the tags in text widget highlight_sample and then invokes
        set_color_sample().  Function set_highlight_target() sets the state
        of the radiobuttons fg_on and bg_on based on the tag and it also
        invokes set_color_sample().

        Function set_color_sample() sets the background color for the frame
        holding the color selector.  This provides a larger visual of the
        color for the current tag and plane (foreground/background).

        Note: set_color_sample() is called from many places and is often
        called more than once when a change is made.  It is invoked when
        foreground or background is selected (radiobuttons), from
        paint_theme_sample() (theme is changed or load_cfg is called), and
        from set_highlight_target() (target tag is changed or load_cfg called).

        Button delete_custom invokes delete_custom() to delete
        a custom theme from pemConf.userCfg['highlight'] and changes.
        Button save_custom invokes save_as_new_theme() which calls
        get_new_theme_name() and create_new() to save a custom theme
        and its colors to pemConf.userCfg['highlight'].

        Radiobuttons fg_on and bg_on toggle var fg_bg_toggle to control
        if the current selected color for a tag is for the foreground or
        background.

        DynOptionMenu targetlist contains a readable description of the
        tags applied to Python source within PEM.  Selecting one of the
        tags from this list populates highlight_target, which has a callback
        function set_highlight_target().

        Text widget highlight_sample displays a block of text (which is
        mock Python code) in which is embedded the defined tags and reflects
        the color attributes of the current theme and changes for those tags.
        Mouse button 1 allows for selection of a tag and updates
        highlight_target with that tag value.

        Note: The font in highlight_sample is set through the config in
        the fonts tab.

        In other words, a tag can be selected either from targetlist or
        by clicking on the sample text within highlight_sample.  The
        plane (foreground/background) is selected via the radiobutton.
        Together, these two (tag and plane) control what color is
        shown in set_color_sample() for the current theme.  Button set_color
        invokes get_color() which displays a ColorChooser to change the
        color for the selected tag/plane.  If a new color is picked,
        it will be saved to changes and the highlight_sample and
        frame background will be updated.

        Tk Variables:
            color: Color of selected target.
            builtin_name: Menu variable for built-in theme.
            custom_name: Menu variable for custom theme.
            fg_bg_toggle: Toggle for foreground/background color.
                Note: this has no callback.
            theme_source: Selector for built-in or custom theme.
            highlight_target: Menu variable for the highlight tag target.

        Instance Data Attributes:
            theme_elements: Dictionary of tags for text highlighting.
                The key is the display name and the value is a tuple of
                (tag name, display sort order).

        Methods [attachment]:
            load_theme_cfg: Load current highlight colors.
            get_color: Invoke colorchooser [button_set_color].
            set_color_sample_binding: Call set_color_sample [fg_bg_toggle].
            set_highlight_target: set fg_bg_toggle, set_color_sample().
            set_color_sample: Set frame background to target.
            on_new_color_set: Set new color and add option.
            paint_theme_sample: Recolor sample.
            get_new_theme_name: Get from popup.
            create_new: Combine theme with changes and save.
            save_as_new_theme: Save [button_save_custom].
            set_theme_type: Command for [theme_source].
            delete_custom: Activate default [button_delete_custom].
            save_new: Save to userCfg['theme'] (is function).

        Widgets of highlights page frame:  (*) widgets bound to self
            frame_custom: LabelFrame
                (*)highlight_sample: Text
                (*)frame_color_set: Frame
                    (*)button_set_color: Button
                    (*)targetlist: DynOptionMenu - highlight_target
                frame_fg_bg_toggle: Frame
                    (*)fg_on: Radiobutton - fg_bg_toggle
                    (*)bg_on: Radiobutton - fg_bg_toggle
                (*)button_save_custom: Button
            frame_theme: LabelFrame
                theme_type_title: Label
                (*)builtin_theme_on: Radiobutton - theme_source
                (*)custom_theme_on: Radiobutton - theme_source
                (*)builtinlist: DynOptionMenu - builtin_name
                (*)customlist: DynOptionMenu - custom_name
                (*)button_delete_custom: Button
                (*)theme_message: Label
        """
        self.theme_elements = {
            # Display-name: internal-config-tag-name.
            'Normal Code or Text': 'normal',
            'Code Context': 'context',
            'Python Keywords': 'keyword',
            'Python Definitions': 'definition',
            'Python Builtins': 'builtin',
            'Python Comments': 'comment',
            'Python Strings': 'string',
            'Selected Text': 'hilite',
            'Found Text': 'hit',
            'Cursor': 'cursor',
            'Console Prompt': 'console',
            'Error Text': 'error',
            'Console User Output': 'stdout',
            'Console User Exception': 'stderr',
            'Line Number': 'linenumber',
            }
        self.builtin_name = tracers.add(
                StringVar(self), self.var_changed_builtin_name)
        self.custom_name = tracers.add(
                StringVar(self), self.var_changed_custom_name)
        self.fg_bg_toggle = BooleanVar(self)
        self.color = tracers.add(
                StringVar(self), self.var_changed_color)
        self.theme_source = tracers.add(
                BooleanVar(self), self.var_changed_theme_source)
        self.highlight_target = tracers.add(
                StringVar(self), self.var_changed_highlight_target)

        # Create widgets:
        # body frame and section frames.
        frame_custom = LabelFrame(self, text=' Custom Highlighting ')
        frame_theme = LabelFrame(self, text=' Highlighting Theme ')
        # frame_custom.
        sample_frame = ScrollableTextFrame(
                frame_custom, relief=SOLID, borderwidth=1)
        text = self.highlight_sample = sample_frame.text
        text.configure(
                font=('courier', 12, ''), cursor='arrow', width=25, height=10,
                takefocus=FALSE, highlightthickness=0, wrap=NONE)
        # Prevent perhaps invisible selection of word or slice.
        text.bind('<Double-Button-1>', lambda e: 'break')
        text.bind('<B1-Motion>', lambda e: 'break')
        string_tags=(
            ('# Click selects item.', 'comment'), ('\n', 'normal'),
            ('code context section', 'context'), ('\n', 'normal'),
            ('| cursor', 'cursor'), ('\n', 'normal'),
            ('def', 'keyword'), (' ', 'normal'),
            ('func', 'definition'), ('(param):\n  ', 'normal'),
            ('"Return None."', 'string'), ('\n  var0 = ', 'normal'),
            ("'string'", 'string'), ('\n  var1 = ', 'normal'),
            ("'selected'", 'hilite'), ('\n  var2 = ', 'normal'),
            ("'found'", 'hit'), ('\n  var3 = ', 'normal'),
            ('list', 'builtin'), ('(', 'normal'),
            ('None', 'keyword'), (')\n\n', 'normal'),
            ('>>>', 'console'), (' 3.14**2\n', 'normal'),
            ('9.8596', 'stdout'), ('\n', 'normal'),
            ('>>>', 'console'), (' pri ', 'normal'),
            ('n', 'error'), ('t(\n', 'normal'),
            ('SyntaxError', 'stderr'), ('\n', 'normal'))
        for string, tag in string_tags:
            text.insert(END, string, tag)
        n_lines = len(text.get('1.0', END).splitlines())
        for lineno in range(1, n_lines):
            text.insert(f'{lineno}.0',
                        f'{lineno:{len(str(n_lines))}d} ',
                        'linenumber')
        for element in self.theme_elements:
            def tem(event, elem=element):
                # event.widget.winfo_top_level().highlight_target.set(elem)
                self.highlight_target.set(elem)
            text.tag_bind(
                    self.theme_elements[element], '<ButtonPress-1>', tem)
        text['state'] = 'disabled'
        self.style.configure('frame_color_set.TFrame', borderwidth=1,
                             relief='solid')
        self.frame_color_set = Frame(frame_custom, style='frame_color_set.TFrame')
        frame_fg_bg_toggle = Frame(frame_custom)
        self.button_set_color = Button(
                self.frame_color_set, text='Choose Color for :',
                command=self.get_color)
        self.targetlist = DynOptionMenu(
                self.frame_color_set, self.highlight_target, None,
                highlightthickness=0) #, command=self.set_highlight_targetBinding
        self.fg_on = Radiobutton(
                frame_fg_bg_toggle, variable=self.fg_bg_toggle, value=1,
                text='Foreground', command=self.set_color_sample_binding)
        self.bg_on = Radiobutton(
                frame_fg_bg_toggle, variable=self.fg_bg_toggle, value=0,
                text='Background', command=self.set_color_sample_binding)
        self.fg_bg_toggle.set(1)
        self.button_save_custom = Button(
                frame_custom, text='Save as New Custom Theme',
                command=self.save_as_new_theme)
        # frame_theme.
        theme_type_title = Label(frame_theme, text='Select : ')
        self.builtin_theme_on = Radiobutton(
                frame_theme, variable=self.theme_source, value=1,
                command=self.set_theme_type, text='a Built-in Theme')
        self.custom_theme_on = Radiobutton(
                frame_theme, variable=self.theme_source, value=0,
                command=self.set_theme_type, text='a Custom Theme')
        self.builtinlist = DynOptionMenu(
                frame_theme, self.builtin_name, None, command=None)
        self.customlist = DynOptionMenu(
                frame_theme, self.custom_name, None, command=None)
        self.button_delete_custom = Button(
                frame_theme, text='Delete Custom Theme',
                command=self.delete_custom)
        self.theme_message = Label(frame_theme, borderwidth=2)
        # Pack widgets:
        # body.
        frame_custom.pack(side=LEFT, padx=5, pady=5, expand=TRUE, fill=BOTH)
        frame_theme.pack(side=TOP, padx=5, pady=5, fill=X)
        # frame_custom.
        self.frame_color_set.pack(side=TOP, padx=5, pady=5, fill=X)
        frame_fg_bg_toggle.pack(side=TOP, padx=5, pady=0)
        sample_frame.pack(
                side=TOP, padx=5, pady=5, expand=TRUE, fill=BOTH)
        self.button_set_color.pack(side=TOP, expand=TRUE, fill=X, padx=8, pady=4)
        self.targetlist.pack(side=TOP, expand=TRUE, fill=X, padx=8, pady=3)
        self.fg_on.pack(side=LEFT, anchor=E)
        self.bg_on.pack(side=RIGHT, anchor=W)
        self.button_save_custom.pack(side=BOTTOM, fill=X, padx=5, pady=5)
        # frame_theme.
        theme_type_title.pack(side=TOP, anchor=W, padx=5, pady=5)
        self.builtin_theme_on.pack(side=TOP, anchor=W, padx=5)
        self.custom_theme_on.pack(side=TOP, anchor=W, padx=5, pady=2)
        self.builtinlist.pack(side=TOP, fill=X, padx=5, pady=5)
        self.customlist.pack(side=TOP, fill=X, anchor=W, padx=5, pady=5)
        self.button_delete_custom.pack(side=TOP, fill=X, padx=5, pady=5)
        self.theme_message.pack(side=TOP, fill=X, pady=5)

    def load_theme_cfg(self):
        """Load current configuration settings for the theme options.

        Based on the theme_source toggle, the theme is set as
        either builtin or custom and the initial widget values
        reflect the current settings from pemConf.

        Attributes updated:
            theme_source: Set from pemConf.
            builtinlist: List of default themes from pemConf.
            customlist: List of custom themes from pemConf.
            custom_theme_on: Disabled if there are no custom themes.
            custom_theme: Message with additional information.
            targetlist: Create menu from self.theme_elements.

        Methods:
            set_theme_type
            paint_theme_sample
            set_highlight_target
        """
        # Set current theme type radiobutton.
        self.theme_source.set(pemConf.GetOption(
                'main', 'Theme', 'default', type='bool', default=1))
        # Set current theme.
        current_option = pemConf.CurrentTheme()
        # Load available theme option menus.
        if self.theme_source.get():  # Default theme selected.
            item_list = pemConf.GetSectionList('default', 'highlight')
            item_list.sort()
            self.builtinlist.SetMenu(item_list, current_option)
            item_list = pemConf.GetSectionList('user', 'highlight')
            item_list.sort()
            if not item_list:
                self.custom_theme_on.state(('disabled',))
                self.custom_name.set('- no custom themes -')
            else:
                self.customlist.SetMenu(item_list, item_list[0])
        else:  # User theme selected.
            item_list = pemConf.GetSectionList('user', 'highlight')
            item_list.sort()
            self.customlist.SetMenu(item_list, current_option)
            item_list = pemConf.GetSectionList('default', 'highlight')
            item_list.sort()
            self.builtinlist.SetMenu(item_list, item_list[0])
        self.set_theme_type()
        # Load theme element option menu.
        theme_names = list(self.theme_elements)
        self.targetlist.SetMenu(theme_names, theme_names[0])
        self.paint_theme_sample()
        self.set_highlight_target()

    def var_changed_builtin_name(self, *params):
        """Process new builtin theme selection.

        Add the changed theme's name to the changed_items and recreate
        the sample with the values from the selected theme.
        """
        old_themes = ('PEM Classic', 'PEM New')
        value = self.builtin_name.get()
        if value not in old_themes:
            if pemConf.GetOption('main', 'Theme', 'name') not in old_themes:
                changes.add_option('main', 'Theme', 'name', old_themes[0])
            changes.add_option('main', 'Theme', 'name2', value)
            self.theme_message['text'] = 'New theme, see Help'
        else:
            changes.add_option('main', 'Theme', 'name', value)
            changes.add_option('main', 'Theme', 'name2', '')
            self.theme_message['text'] = ''
        self.paint_theme_sample()

    def var_changed_custom_name(self, *params):
        """Process new custom theme selection.

        If a new custom theme is selected, add the name to the
        changed_items and apply the theme to the sample.
        """
        value = self.custom_name.get()
        if value != '- no custom themes -':
            changes.add_option('main', 'Theme', 'name', value)
            self.paint_theme_sample()

    def var_changed_theme_source(self, *params):
        """Process toggle between builtin and custom theme.

        Update the default toggle value and apply the newly
        selected theme type.
        """
        value = self.theme_source.get()
        changes.add_option('main', 'Theme', 'default', value)
        if value:
            self.var_changed_builtin_name()
        else:
            self.var_changed_custom_name()

    def var_changed_color(self, *params):
        "Process change to color choice."
        self.on_new_color_set()

    def var_changed_highlight_target(self, *params):
        "Process selection of new target tag for highlighting."
        self.set_highlight_target()

    def set_theme_type(self):
        """Set available screen options based on builtin or custom theme.

        Attributes accessed:
            theme_source

        Attributes updated:
            builtinlist
            customlist
            button_delete_custom
            custom_theme_on

        Called from:
            handler for builtin_theme_on and custom_theme_on
            delete_custom
            create_new
            load_theme_cfg
        """
        if self.theme_source.get():
            self.builtinlist['state'] = 'normal'
            self.customlist['state'] = 'disabled'
            self.button_delete_custom.state(('disabled',))
        else:
            self.builtinlist['state'] = 'disabled'
            self.custom_theme_on.state(('!disabled',))
            self.customlist['state'] = 'normal'
            self.button_delete_custom.state(('!disabled',))

    def get_color(self):
        """Handle button to select a new color for the target tag.

        If a new color is selected while using a builtin theme, a
        name must be supplied to create a custom theme.

        Attributes accessed:
            highlight_target
            frame_color_set
            theme_source

        Attributes updated:
            color

        Methods:
            get_new_theme_name
            create_new
        """
        target = self.highlight_target.get()
        prev_color = self.style.lookup(self.frame_color_set['style'],
                                       'background')
        rgbTuplet, color_string = colorchooser.askcolor(
                parent=self, title='Pick new color for : '+target,
                initialcolor=prev_color)
        if color_string and (color_string != prev_color):
            # User didn't cancel and they chose a new color.
            if self.theme_source.get():  # Current theme is a built-in.
                message = ('Your changes will be saved as a new Custom Theme. '
                           'Enter a name for your new Custom Theme below.')
                new_theme = self.get_new_theme_name(message)
                if not new_theme:  # User cancelled custom theme creation.
                    return
                else:  # Create new custom theme based on previously active theme.
                    self.create_new(new_theme)
                    self.color.set(color_string)
            else:  # Current theme is user defined.
                self.color.set(color_string)

    def on_new_color_set(self):
        "Display sample of new color selection on the dialog."
        new_color = self.color.get()
        self.style.configure('frame_color_set.TFrame', background=new_color)
        plane = 'foreground' if self.fg_bg_toggle.get() else 'background'
        sample_element = self.theme_elements[self.highlight_target.get()]
        self.highlight_sample.tag_config(sample_element, **{plane: new_color})
        theme = self.custom_name.get()
        theme_element = sample_element + '-' + plane
        changes.add_option('highlight', theme, theme_element, new_color)

    def get_new_theme_name(self, message):
        "Return name of new theme from query popup."
        used_names = (pemConf.GetSectionList('user', 'highlight') +
                pemConf.GetSectionList('default', 'highlight'))
        new_theme = SectionName(
                self, 'New Custom Theme', message, used_names).result
        return new_theme

    def save_as_new_theme(self):
        """Prompt for new theme name and create the theme.

        Methods:
            get_new_theme_name
            create_new
        """
        new_theme_name = self.get_new_theme_name('New Theme Name:')
        if new_theme_name:
            self.create_new(new_theme_name)

    def create_new(self, new_theme_name):
        """Create a new custom theme with the given name.

        Create the new theme based on the previously active theme
        with the current changes applied.  Once it is saved, then
        activate the new theme.

        Attributes accessed:
            builtin_name
            custom_name

        Attributes updated:
            customlist
            theme_source

        Method:
            save_new
            set_theme_type
        """
        if self.theme_source.get():
            theme_type = 'default'
            theme_name = self.builtin_name.get()
        else:
            theme_type = 'user'
            theme_name = self.custom_name.get()
        new_theme = pemConf.GetThemeDict(theme_type, theme_name)
        # Apply any of the old theme's unsaved changes to the new theme.
        if theme_name in changes['highlight']:
            theme_changes = changes['highlight'][theme_name]
            for element in theme_changes:
                new_theme[element] = theme_changes[element]
        # Save the new theme.
        self.save_new(new_theme_name, new_theme)
        # Change GUI over to the new theme.
        custom_theme_list = pemConf.GetSectionList('user', 'highlight')
        custom_theme_list.sort()
        self.customlist.SetMenu(custom_theme_list, new_theme_name)
        self.theme_source.set(0)
        self.set_theme_type()

    def set_highlight_target(self):
        """Set fg/bg toggle and color based on highlight tag target.

        Instance variables accessed:
            highlight_target

        Attributes updated:
            fg_on
            bg_on
            fg_bg_toggle

        Methods:
            set_color_sample

        Called from:
            var_changed_highlight_target
            load_theme_cfg
        """
        if self.highlight_target.get() == 'Cursor':  # bg not possible
            self.fg_on.state(('disabled',))
            self.bg_on.state(('disabled',))
            self.fg_bg_toggle.set(1)
        else:  # Both fg and bg can be set.
            self.fg_on.state(('!disabled',))
            self.bg_on.state(('!disabled',))
            self.fg_bg_toggle.set(1)
        self.set_color_sample()

    def set_color_sample_binding(self, *args):
        """Change color sample based on foreground/background toggle.

        Methods:
            set_color_sample
        """
        self.set_color_sample()

    def set_color_sample(self):
        """Set the color of the frame background to reflect the selected target.

        Instance variables accessed:
            theme_elements
            highlight_target
            fg_bg_toggle
            highlight_sample

        Attributes updated:
            frame_color_set
        """
        # Set the color sample area.
        tag = self.theme_elements[self.highlight_target.get()]
        plane = 'foreground' if self.fg_bg_toggle.get() else 'background'
        color = self.highlight_sample.tag_cget(tag, plane)
        self.style.configure('frame_color_set.TFrame', background=color)

    def paint_theme_sample(self):
        """Apply the theme colors to each element tag in the sample text.

        Instance attributes accessed:
            theme_elements
            theme_source
            builtin_name
            custom_name

        Attributes updated:
            highlight_sample: Set the tag elements to the theme.

        Methods:
            set_color_sample

        Called from:
            var_changed_builtin_name
            var_changed_custom_name
            load_theme_cfg
        """
        if self.theme_source.get():  # Default theme
            theme = self.builtin_name.get()
        else:  # User theme
            theme = self.custom_name.get()
        for element_title in self.theme_elements:
            element = self.theme_elements[element_title]
            colors = pemConf.GetHighlight(theme, element)
            if element == 'cursor':  # Cursor sample needs special painting.
                colors['background'] = pemConf.GetHighlight(
                        theme, 'normal')['background']
            # Handle any unsaved changes to this theme.
            if theme in changes['highlight']:
                theme_dict = changes['highlight'][theme]
                if element + '-foreground' in theme_dict:
                    colors['foreground'] = theme_dict[element + '-foreground']
                if element + '-background' in theme_dict:
                    colors['background'] = theme_dict[element + '-background']
            self.highlight_sample.tag_config(element, **colors)
        self.set_color_sample()

    def save_new(self, theme_name, theme):
        """Save a newly created theme to pemConf.

        theme_name - string, the name of the new theme
        theme - dictionary containing the new theme
        """
        pemConf.userCfg['highlight'].AddSection(theme_name)
        for element in theme:
            value = theme[element]
            pemConf.userCfg['highlight'].SetOption(theme_name, element, value)

    def askyesno(self, *args, **kwargs):
        # Make testing easier.  Could change implementation.
        return messagebox.askyesno(*args, **kwargs)

    def delete_custom(self):
        """Handle event to delete custom theme.

        The current theme is deactivated and the default theme is
        activated.  The custom theme is permanently removed from
        the config file.

        Attributes accessed:
            custom_name

        Attributes updated:
            custom_theme_on
            customlist
            theme_source
            builtin_name

        Methods:
            deactivate_current_config
            save_all_changed_extensions
            activate_config_changes
            set_theme_type
        """
        theme_name = self.custom_name.get()
        delmsg = 'Are you sure you wish to delete the theme %r ?'
        if not self.askyesno(
                'Delete Theme',  delmsg % theme_name, parent=self):
            return
        self.cd.deactivate_current_config()
        # Remove theme from changes, config, and file.
        changes.delete_section('highlight', theme_name)
        # Reload user theme list.
        item_list = pemConf.GetSectionList('user', 'highlight')
        item_list.sort()
        if not item_list:
            self.custom_theme_on.state(('disabled',))
            self.customlist.SetMenu(item_list, '- no custom themes -')
        else:
            self.customlist.SetMenu(item_list, item_list[0])
        # Revert to default theme.
        self.theme_source.set(pemConf.defaultCfg['main'].Get('Theme', 'default'))
        self.builtin_name.set(pemConf.defaultCfg['main'].Get('Theme', 'name'))
        # User can't back out of these changes, they must be applied now.
        changes.save_all()
        self.extpage.save_all_changed_extensions()
        self.cd.activate_config_changes()
        self.set_theme_type()


# *** PEM Edit: KeysPage removed
# class KeysPage(Frame):


# *** PEM Edit: WinPage removed
# class WinPage(Frame):


# *** PEM Edit: ShedPage removed
# class ShedPage(Frame):


class ExtPage(Frame):
    "Settings dialog tab: enable/disable extensions and edit their options."

    def __init__(self, master):
        super().__init__(master)
        self.ext_defaultCfg = pemConf.defaultCfg['extensions']
        self.ext_userCfg = pemConf.userCfg['extensions']
        self.is_int = self.register(is_int)
        self.load_extensions()
        self.create_page_extensions()  # Requires extension names.

    def create_page_extensions(self):
        """Configure PEM feature extensions and help menu extensions.

        List the feature extensions and a configuration box for the
        selected extension.  Help menu extensions are in a HelpFrame.

        This code reads the current configuration using pemConf,
        supplies a GUI interface to change the configuration values,
        and saves the changes using pemConf.

        Some changes may require restarting PEM.  This depends on each
        extension's implementation.

        All values are treated as text, and it is up to the user to
        supply reasonable values. The only exception to this are the
        'enable*' options, which are boolean, and can be toggled with a
        True/False button.

        Methods:
            extension_selected: Handle selection from list.
            create_extension_frame: Hold widgets for one extension.
            set_extension_value: Set in userCfg['extensions'].
            save_all_changed_extensions: Call extension page Save().
        """
        self.extension_names = StringVar(self)

        frame_ext = LabelFrame(self, text=' Feature Extensions ')
        self.frame_help = HelpFrame(self, text=' Help Menu Extensions ')

        frame_ext.rowconfigure(0, weight=1)
        frame_ext.columnconfigure(2, weight=1)
        self.extension_list = Listbox(frame_ext, listvariable=self.extension_names,
                                      selectmode='browse')
        self.extension_list.bind('<<ListboxSelect>>', self.extension_selected)
        scroll = Scrollbar(frame_ext, command=self.extension_list.yview)
        self.extension_list.yscrollcommand=scroll.set
        self.details_frame = LabelFrame(frame_ext, width=250, height=250)
        self.extension_list.grid(column=0, row=0, sticky='nws')
        scroll.grid(column=1, row=0, sticky='ns')
        self.details_frame.grid(column=2, row=0, sticky='nsew', padx=[10, 0])
        frame_ext.configure(padding=10)
        self.config_frame = {}
        self.current_extension = None

        self.outerframe = self                      # TEMPORARY
        self.tabbed_page_set = self.extension_list  # TEMPORARY

        # Create the frame holding controls for each extension.
        ext_names = ''
        for ext_name in sorted(self.extensions):
            self.create_extension_frame(ext_name)
            ext_names = ext_names + '{' + ext_name + '} '
        self.extension_names.set(ext_names)
        self.extension_list.selection_set(0)
        self.extension_selected(None)


        frame_ext.grid(row=0, column=0, sticky='nsew')
        Label(self).grid(row=1, column=0)  # Spacer.  Replace with config?
        self.frame_help.grid(row=2, column=0, sticky='sew')

    def load_extensions(self):
        "Fill self.extensions with data from the default and user configs."
        self.extensions = {}
        for ext_name in pemConf.GetExtensions(active_only=False):
            # Former built-in extensions are already filtered out.
            self.extensions[ext_name] = []

        for ext_name in self.extensions:
            opt_list = sorted(self.ext_defaultCfg.GetOptionList(ext_name))

            # Bring 'enable' options to the beginning of the list.
            enables = [opt_name for opt_name in opt_list
                       if opt_name.startswith('enable')]
            for opt_name in enables:
                opt_list.remove(opt_name)
            opt_list = enables + opt_list

            for opt_name in opt_list:
                def_str = self.ext_defaultCfg.Get(
                        ext_name, opt_name, raw=True)
                try:
                    def_obj = {'True':True, 'False':False}[def_str]
                    opt_type = 'bool'
                except KeyError:
                    try:
                        def_obj = int(def_str)
                        opt_type = 'int'
                    except ValueError:
                        def_obj = def_str
                        opt_type = None
                try:
                    value = self.ext_userCfg.Get(
                            ext_name, opt_name, type=opt_type, raw=True,
                            default=def_obj)
                except ValueError:  # Need this until .Get fixed.
                    value = def_obj  # Bad values overwritten by entry.
                var = StringVar(self)
                var.set(str(value))

                self.extensions[ext_name].append({'name': opt_name,
                                                  'type': opt_type,
                                                  'default': def_str,
                                                  'value': value,
                                                  'var': var,
                                                 })

    def extension_selected(self, event):
        "Handle selection of an extension from the list."
        newsel = self.extension_list.curselection()
        if newsel:
            newsel = self.extension_list.get(newsel)
        if newsel is None or newsel != self.current_extension:
            if self.current_extension:
                self.details_frame.config(text='')
                self.config_frame[self.current_extension].grid_forget()
                self.current_extension = None
        if newsel:
            self.details_frame.config(text=newsel)
            self.config_frame[newsel].grid(column=0, row=0, sticky='nsew')
            self.current_extension = newsel

    def create_extension_frame(self, ext_name):
        """Create a frame holding the widgets to configure one extension"""
        f = VerticalScrolledFrame(self.details_frame, height=250, width=250)
        self.config_frame[ext_name] = f
        entry_area = f.interior
        # Create an entry for each configuration option.
        for row, opt in enumerate(self.extensions[ext_name]):
            # Create a row with a label and entry/checkbutton.
            label = Label(entry_area, text=opt['name'])
            label.grid(row=row, column=0, sticky=NW)
            var = opt['var']
            if opt['type'] == 'bool':
                Checkbutton(entry_area, variable=var,
                            onvalue='True', offvalue='False', width=8
                            ).grid(row=row, column=1, sticky=W, padx=7)
            elif opt['type'] == 'int':
                Entry(entry_area, textvariable=var, validate='key',
                      validatecommand=(self.is_int, '%P'), width=10
                      ).grid(row=row, column=1, sticky=NSEW, padx=7)

            else:  # type == 'str'
                # Limit size to fit non-expanding space with larger font.
                Entry(entry_area, textvariable=var, width=15
                      ).grid(row=row, column=1, sticky=NSEW, padx=7)
        return

    def set_extension_value(self, section, opt):
        """Return True if the configuration was added or changed.

        If the value is the same as the default, then remove it
        from user config file.
        """
        name = opt['name']
        default = opt['default']
        value = opt['var'].get().strip() or default
        opt['var'].set(value)
        # if self.defaultCfg.has_section(section):
        # Currently, always true; if not, indent to return.
        if (value == default):
            return self.ext_userCfg.RemoveOption(section, name)
        # Set the option.
        return self.ext_userCfg.SetOption(section, name, value)

    def save_all_changed_extensions(self):
        """Save configuration changes to the user config file.

        Attributes accessed:
            extensions

        Methods:
            set_extension_value
        """
        has_changes = False
        for ext_name in self.extensions:
            options = self.extensions[ext_name]
            for opt in options:
                if self.set_extension_value(ext_name, opt):
                    has_changes = True
        if has_changes:
            self.ext_userCfg.Save()


class HelpFrame(LabelFrame):
    "The 'Additional Help Sources' editor embedded in the General tab."

    def __init__(self, master, **cfg):
        super().__init__(master, **cfg)
        self.create_frame_help()
        self.load_helplist()

    def create_frame_help(self):
        """Create LabelFrame for additional help menu sources.

        load_helplist loads list user_helplist with
        name, position pairs and copies names to listbox helplist.
        Clicking a name invokes help_source selected. Clicking
        button_helplist_name invokes helplist_item_name, which also
        changes user_helplist.  These functions all call
        set_add_delete_state. All but load call update_help_changes to
        rewrite changes['main']['HelpFiles'].

        Widgets for HelpFrame(LabelFrame):  (*) widgets bound to self
            frame_helplist: Frame
                (*)helplist: ListBox
                scroll_helplist: Scrollbar
            frame_buttons: Frame
                (*)button_helplist_edit
                (*)button_helplist_add
                (*)button_helplist_remove
        """
        # self = frame_help in dialog (until ExtPage class).
        frame_helplist = Frame(self)
        self.helplist = Listbox(
                frame_helplist, height=5, takefocus=True,
                exportselection=FALSE)
        scroll_helplist = Scrollbar(frame_helplist)
        scroll_helplist['command'] = self.helplist.yview
        self.helplist['yscrollcommand'] = scroll_helplist.set
        self.helplist.bind('<ButtonRelease-1>', self.help_source_selected)

        frame_buttons = Frame(self)
        self.button_helplist_edit = Button(
                frame_buttons, text='Edit', state='disabled',
                width=8, command=self.helplist_item_edit)
        self.button_helplist_add = Button(
                frame_buttons, text='Add',
                width=8, command=self.helplist_item_add)
        self.button_helplist_remove = Button(
                frame_buttons, text='Remove', state='disabled',
                width=8, command=self.helplist_item_remove)

        # Pack frame_help.
        frame_helplist.pack(side=LEFT, padx=5, pady=5, expand=TRUE, fill=BOTH)
        self.helplist.pack(side=LEFT, anchor=E, expand=TRUE, fill=BOTH)
        scroll_helplist.pack(side=RIGHT, anchor=W, fill=Y)
        frame_buttons.pack(side=RIGHT, padx=5, pady=5, fill=Y)
        self.button_helplist_edit.pack(side=TOP, anchor=W, pady=5)
        self.button_helplist_add.pack(side=TOP, anchor=W)
        self.button_helplist_remove.pack(side=TOP, anchor=W, pady=5)

    def help_source_selected(self, event):
        "Handle event for selecting additional help."
        self.set_add_delete_state()

    def set_add_delete_state(self):
        "Toggle the state for the help list buttons based on list entries."
        if self.helplist.size() < 1:  # No entries in list.
            self.button_helplist_edit.state(('disabled',))
            self.button_helplist_remove.state(('disabled',))
        else:  # Some entries.
            if self.helplist.curselection():  # There currently is a selection.
                self.button_helplist_edit.state(('!disabled',))
                self.button_helplist_remove.state(('!disabled',))
            else:  # There currently is not a selection.
                self.button_helplist_edit.state(('disabled',))
                self.button_helplist_remove.state(('disabled',))

    def helplist_item_add(self):
        """Handle add button for the help list.

        Query for name and location of new help sources and add
        them to the list.
        """
        help_source = HelpSource(self, 'New Help Source').result
        if help_source:
            self.user_helplist.append(help_source)
            self.helplist.insert(END, help_source[0])
            self.update_help_changes()

    def helplist_item_edit(self):
        """Handle edit button for the help list.

        Query with existing help source information and update
        config if the values are changed.
        """
        item_index = self.helplist.index(ANCHOR)
        help_source = self.user_helplist[item_index]
        new_help_source = HelpSource(
                self, 'Edit Help Source',
                menuitem=help_source[0],
                filepath=help_source[1],
                ).result
        if new_help_source and new_help_source != help_source:
            self.user_helplist[item_index] = new_help_source
            self.helplist.delete(item_index)
            self.helplist.insert(item_index, new_help_source[0])
            self.update_help_changes()
            self.set_add_delete_state()  # Selected will be un-selected

    def helplist_item_remove(self):
        """Handle remove button for the help list.

        Delete the help list item from config.
        """
        item_index = self.helplist.index(ANCHOR)
        del(self.user_helplist[item_index])
        self.helplist.delete(item_index)
        self.update_help_changes()
        self.set_add_delete_state()

    def update_help_changes(self):
        "Clear and rebuild the HelpFiles section in changes"
        changes['main']['HelpFiles'] = {}
        for num in range(1, len(self.user_helplist) + 1):
            changes.add_option(
                    'main', 'HelpFiles', str(num),
                    ';'.join(self.user_helplist[num-1][:2]))

    def load_helplist(self):
        # Set additional help sources.
        self.user_helplist = pemConf.GetAllExtraHelpSourcesList()
        self.helplist.delete(0, 'end')
        for help_item in self.user_helplist:
            self.helplist.insert(END, help_item[0])
        self.set_add_delete_state()


class VarTrace:
    """Maintain Tk variables trace state."""

    def __init__(self):
        """Store Tk variables and callbacks.

        untraced: List of tuples (var, callback)
            that do not have the callback attached
            to the Tk var.
        traced: List of tuples (var, callback) where
            that callback has been attached to the var.
        """
        self.untraced = []
        self.traced = []

    def clear(self):
        "Clear lists (for tests)."
        # Call after all tests in a module to avoid memory leaks.
        self.untraced.clear()
        self.traced.clear()

    def add(self, var, callback):
        """Add (var, callback) tuple to untraced list.

        Args:
            var: Tk variable instance.
            callback: Either function name to be used as a callback
                or a tuple with PemConf config-type, section, and
                option names used in the default callback.

        Return:
            Tk variable instance.
        """
        if isinstance(callback, tuple):
            callback = self.make_callback(var, callback)
        self.untraced.append((var, callback))
        return var

    @staticmethod
    def make_callback(var, config):
        "Return default callback function to add values to changes instance."
        def default_callback(*params):
            "Add config values to changes instance."
            changes.add_option(*config, var.get())
        return default_callback

    def attach(self):
        "Attach callback to all vars that are not traced."
        while self.untraced:
            var, callback = self.untraced.pop()
            var.trace_add('write', callback)
            self.traced.append((var, callback))

    def detach(self):
        "Remove callback from traced vars."
        while self.traced:
            var, callback = self.traced.pop()
            var.trace_remove('write', var.trace_info()[0][1])
            self.untraced.append((var, callback))


tracers = VarTrace()

help_common = '''\
When you click either the Apply or Ok buttons, settings in this
dialog that are different from PEM's default are saved in
a .pemrc directory in your home directory. Except as noted,
these changes apply to all versions of PEM installed on this
machine. [Cancel] only cancels changes made since the last save.
'''
help_pages = {
    'General': '''
General Preferences:

Font Size: Set the default font size for the editor and console.
Indent Width: Set the number of spaces for indentation.
Automatic Indent: When checked, PEM will automatically indent new lines.
Highlight Current Line: When checked, the current line will be highlighted (Functionality TBD).
Show Code Context: When checked, the code context will be displayed at the top of the window.
Auto Save Before Run: When checked, PEM will automatically save your script before running. When unchecked, a temporary file is used allowing you to run without saving.
''',
    'Style': '''
Style Preferences:
Customize foreground and background colors applied to textual tags.
Themes can be selected from built-in options or custom user themes.
''',
}
# *** PEM Edit: Removed older help pages for Fonts, Keys, Windows, Console/Editor, and Extensions.


def is_int(s):
    "Return 's is blank or represents an int'"
    if not s:
        return True
    try:
        int(s)
        return True
    except ValueError:
        return False


class VerticalScrolledFrame(Frame):
    """A pure Tkinter vertically scrollable frame.

    * Use the 'interior' attribute to place widgets inside the scrollable frame
    * Construct and pack/place/grid normally
    * This frame only allows vertical scrolling
    """
    def __init__(self, parent, *args, **kw):
        Frame.__init__(self, parent, *args, **kw)

        # Create a canvas object and a vertical scrollbar for scrolling it.
        vscrollbar = Scrollbar(self, orient=VERTICAL)
        vscrollbar.pack(fill=Y, side=RIGHT, expand=FALSE)
        canvas = Canvas(self, borderwidth=0, highlightthickness=0,
                        yscrollcommand=vscrollbar.set, width=240)
        canvas.pack(side=LEFT, fill=BOTH, expand=TRUE)
        vscrollbar.config(command=canvas.yview)

        # Reset the view.
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        # Create a frame inside the canvas which will be scrolled with it.
        self.interior = interior = Frame(canvas)
        interior_id = canvas.create_window(0, 0, window=interior, anchor=NW)

        # Track changes to the canvas and frame width and sync them,
        # also updating the scrollbar.
        def _configure_interior(event):
            # Update the scrollbars to match the size of the inner frame.
            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
        interior.bind('<Configure>', _configure_interior)

        def _configure_canvas(event):
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # Update the inner frame's width to fill the canvas.
                canvas.itemconfigure(interior_id, width=canvas.winfo_width())
        canvas.bind('<Configure>', _configure_canvas)

        return


if __name__ == '__main__':
    from unittest import main
    main('pem.pem_test.test_configdialog', verbosity=2, exit=False)

    from pem.pem_test.htest import run
    run(ConfigDialog)
