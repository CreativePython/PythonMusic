"""Run code from an editor window in the execution subprocess.

``ScriptBinding`` backs the Run menu / toolbar:

  * check module -- full syntax check + tabnanny, no execution;
  * run module   -- syntax-check, then exec the whole file in __main__ (after a
        fresh subprocess restart, unless "Customize Run" opts out); the file is
        saved, or copied to a temp buffer, first if it has unsaved edits;
  * run selection / current line / current paragraph -- exec just that snippet
        in the existing namespace, no restart.

Each run's output goes to the editor tab's own output pane -- see
``_prepare_for_run`` and ``PyShell.set_active_sink``.
"""
import os
import tabnanny
import tempfile
import time
import tokenize

from tkinter import messagebox, TclError

from pem.config import pemConf
from pem import macosx
from pem import perflog
from pem import pyshell
from pem.dialogs.query import CustomRun
from pem.shell import outwin

indent_message = """Error: Inconsistent indentation detected!

1) Your indentation is outright incorrect (easy to fix), OR
2) Your indentation mixes tabs and spaces.

To fix case 2, change all tabs to spaces by using Edit->Select All followed \
by Format->Untabify Region and specify the number of columns used by each tab.
"""


class ScriptBinding:
    "Run-menu / Run-toolbar behaviour for one editor window."

    def __init__(self, editwin):
        self.editwin = editwin
        self.flist = self.editwin.flist
        self.root = self.editwin.root
        self.cli_args = []
        self.perf = 0.0    # Workaround for macOS 11 Uni2; see bpo-42508.
        self.bufferTempfile = None   
        self.runHighlightCounter = 0   
        self.HIGHLIGHT_DURATION = 750   

    # -------------------------------------------------------------------------
    # SUBSYSTEM: PREPARE FOR RUN
    # -------------------------------------------------------------------------
    def _prepare_for_run(self):
        """Boot the execution subprocess if needed and route this run's output
        to this tab's output pane.

        Returns True if a usable PyShell backend is available, False otherwise
        (the caller should abort the run rather than crash).  Output routing is
        done by PyShell.write / PyShell.readline dispatching on
        PyShell.active_sink, which set_active_sink() points at this editwin.
        """
        perflog.mark("_prepare_for_run: begin")
        # Boot the background Python subprocess if it does not exist yet.
        if not getattr(self.flist, 'pyshell', None):
            perflog.mark("_prepare_for_run: no PyShell yet -> creating + begin()")
            try:
                self.flist.pyshell = pyshell.PyShell(self.flist)
                if self.flist.pyshell:
                    if self.flist.pyshell.top:
                        self.flist.pyshell.top.withdraw()  # boot silently, hidden
                    # begin() may close (and null out flist.pyshell) on failure.
                    self.flist.pyshell.begin()
            except Exception:
                self.flist.pyshell = None
            perflog.mark("_prepare_for_run: PyShell boot attempt done")

        self.shell = getattr(self.flist, 'pyshell', None)
        if self.shell is None or not hasattr(self.shell, 'set_active_sink'):
            self.shell = None
            try:
                self.editwin.text.bell()
            except Exception:
                pass
            return False

        # Route this run's output to this tab's output pane, and clear the pane
        # so only the new run's output shows.
        self.shell.set_active_sink(self.editwin)
        if hasattr(self.editwin, 'clear_output'):
            self.editwin.clear_output()
        return True


    # -------------------------------------------------------------------------
    # EXECUTION EVENTS
    # -------------------------------------------------------------------------
    def check_module_event(self, event):
        if isinstance(self.editwin, outwin.OutputWindow):
            self.editwin.text.bell()
            return 'break'
        filename = self.getfilename()
        if not filename:
            return 'break'

        # Lock routing BEFORE checking syntax to properly catch tracebacks
        if not self._prepare_for_run():
            return 'break'

        if not self.checksyntax(filename, self._sourceFilename(filename)):
            return 'break'
        if not self.tabnanny(filename):
            return 'break'
        return "break"

    def tabnanny(self, filename):
        with tokenize.open(filename) as f:
            try:
                tabnanny.process_tokens(tokenize.generate_tokens(f.readline))
            except tokenize.TokenError as msg:
                msgtxt, (lineno, start) = msg.args
                self.editwin.gotoline(lineno)
                self.errorbox("Tabnanny Tokenizing Error",
                              "Token Error: %s" % msgtxt)
                return False
            except tabnanny.NannyNag as nag:
                self.editwin.gotoline(nag.get_lineno())
                self.errorbox("Tab/space error", indent_message)
                return False
        return True

    def checksyntax(self, filename, compileName=None):
        # `filename` is where we read bytes from (the temp buffer when running
        # unsaved edits); `compileName` is the user-facing source path baked
        # into co_filename, so tracebacks, __file__, and inspect.stack()-based
        # path resolution all see the saved file's location, not /tmp/...
        shell = getattr(self, 'shell', None)
        if not shell:
            shell = self.flist.open_shell()

        saved_stream = shell.get_warning_stream()
        shell.set_warning_stream(shell.stderr)
        with open(filename, 'rb') as f:
            source = f.read()

        if b'\r' in source:
            source = source.replace(b'\r\n', b'\n')
            source = source.replace(b'\r', b'\n')
        if source and source[-1] != ord(b'\n'):
            source = source + b'\n'

        editwin = self.editwin
        text = editwin.text
        text.tag_remove("ERROR", "1.0", "end")

        try:
            return compile(source, compileName or filename, "exec")
        except (SyntaxError, OverflowError, ValueError) as value:
            msg = getattr(value, 'msg', '') or value or "<no detail available>"
            lineno = getattr(value, 'lineno', '') or 1
            offset = getattr(value, 'offset', '') or 0
            if offset == 0:
                lineno += 1  
            pos = "0.0 + %d lines + %d chars" % (lineno-1, offset-1)
            editwin.colorize_syntax_error(text, pos)
            self.errorbox("SyntaxError", "%-20s" % msg)
            return False
        finally:
            shell.set_warning_stream(saved_stream)

    def run_custom_event(self, event):
        return self.run_module_event(event, customize=True)

    def run_module_event(self, event, *, customize=False):
        """Prepares the background namespace and executes the full module."""
        perflog.mark("run_module_event: Run pressed")
        if macosx.isCocoaTk() and (time.perf_counter() - self.perf < .05):
            return 'break'
        if isinstance(self.editwin, outwin.OutputWindow):
            self.editwin.text.bell()
            return 'break'
            
        filename = self.getfilename()
        if not filename:
            return 'break'

        if not self._prepare_for_run():
            self._cleanupBufferTempfile()
            return 'break'

        displayFilename = self._sourceFilename(filename)
        code = self.checksyntax(filename, displayFilename)
        if not code:
            self._cleanupBufferTempfile()
            return 'break'
        if not self.tabnanny(filename):
            self._cleanupBufferTempfile()
            return 'break'

        if customize:
            title = f"Customize {self.editwin.short_title()} Run"
            run_args = CustomRun(self.shell.text, title,
                                 cli_args=self.cli_args).result
            if not run_args:
                return 'break'
            self.cli_args, restart = run_args
        else:
            self.cli_args, restart = [], True
        interp = self.shell.interp

        # Working dir mirrors displayFilename so relative asset paths in the
        # user's script resolve against the saved file's folder, not /tmp/.
        if self.bufferTempfile and not self.editwin.io.filename:
            workingDir = self.editwin.io.dirname or os.path.expanduser('~')
        else:
            workingDir = os.path.dirname(os.path.abspath(displayFilename))
            
        # Manage Subprocess Lifecycles
        if restart:
            interp.restart_subprocess(
                    with_cwd=False, filename=displayFilename)
        else:
            # "Customize Run" with "Restart" unchecked: run on top of the
            # existing namespace.  Note it in the Console (write_to_console
            # bypasses the active-sink dispatch).
            base = os.path.basename(displayFilename)
            self.shell.write_to_console(
                f"\n------- {base} (no restart) -------\n", "stdout")
            self.shell.text.mark_set("restart", "end-1c")
            self.shell.text.mark_gravity("restart", "left")
            
        argv = [displayFilename]
        if self.cli_args:
            argv += self.cli_args
            
        self.flist.interp_cwd = workingDir
        # Set up __file__, sys.argv, cwd and sys.path[0] in the subprocess in a
        # single RPC round-trip before the code runs.
        interp.runcommand(f"""if 1:
            __file__ = {displayFilename!r}
            import sys as _sys
            import os as _os
            from os.path import basename as _basename, dirname as _dirname
            argv = {argv!r}
            if (not _sys.argv or
                _basename(_sys.argv[0]) != _basename(__file__) or
                len(argv) > 1):
                _sys.argv = argv
            _os.chdir({workingDir!r})
            _dir = _dirname(__file__)
            if not _dir in _sys.path:
                _sys.path.insert(0, _dir)
            del _sys, _os, _basename, _dirname, argv, _dir
            \n""")

        # self.flist.set_run_indicator(True)
        perflog.mark("run_module_event: handing compiled code to interp.runcode")
        interp.runcode(code)

        self._cleanupBufferTempfile()
        return 'break'

    # -------------------------------------------------------------------------
    # UTILITIES AND PARTIAL EXECUTION
    # -------------------------------------------------------------------------
    def _sourceFilename(self, filename):
        """Return the user-facing source path for compile()/__file__/argv.

        When running unsaved edits, `filename` points at the throwaway temp
        buffer in /tmp; the saved file's path (or the tab's short title for
        never-saved buffers) is what should be baked into co_filename so
        tracebacks and inspect.stack()-based path resolution (AudioSample,
        Read.midi) see the location the user is editing, not /tmp.
        """
        if self.bufferTempfile:
            return self.editwin.io.filename or self.editwin.short_title()
        return filename

    def getfilename(self):
        """Retrieve the source filename or establish a temp buffer if autosave is off."""
        filename = self.editwin.io.filename
        if not self.editwin.get_saved():
            autosave = pemConf.GetOption('main', 'General',
                                          'autosave', type='bool')
            if autosave:
                self.editwin.io.save(None)
                filename = self.editwin.io.filename
            else:
                return self._createBufferTempfile()
        return filename

    def ask_save_dialog(self):
        msg = "Source Must Be Saved\n" + 5*' ' + "OK to Save?"
        confirm = messagebox.askokcancel(title="Save Before Run or Check",
                                         message=msg,
                                         default=messagebox.OK,
                                         parent=self.editwin.text)
        return confirm

    def _cleanupBufferTempfile(self):
        """Purge the temporary text buffer file from memory and disk."""
        if self.bufferTempfile:
            try:
                os.unlink(self.bufferTempfile)
            except OSError:
                pass   
            self.bufferTempfile = None

    def _createBufferTempfile(self):
        """Establish a temporary script buffer for execution without overriding saved files."""
        self._cleanupBufferTempfile()
        filename = self.editwin.io.filename
        extension = os.path.splitext(filename)[1] if filename else '.py'
        if not extension:
            extension = '.py'

        try:
            fd, bufferTempFilename = tempfile.mkstemp(
                prefix='PEM_buffer_',
                suffix=extension
            )
            os.close(fd)   
            if not self.editwin.io.writefile(bufferTempFilename):
                try:
                    os.unlink(bufferTempFilename)
                except OSError:
                    pass
                return None
            self.bufferTempfile = bufferTempFilename
            return bufferTempFilename
        except OSError as err:
            self.errorbox("Temp File Error",
                         f"Could not create temporary file:\n{err}")
            return None

    def errorbox(self, title, message):
        messagebox.showerror(title, message, parent=self.editwin.text)
        self.editwin.text.focus_set()
        self.perf = time.perf_counter()

    def highlightRunCode(self, startPos, endPos):
        """Temporarily highlights code blocks being executed for visual feedback."""
        text = self.editwin.text
        hiliteColors = pemConf.GetHighlight(pemConf.CurrentTheme(), "hilite")
        text.tag_configure("run-highlight",
                          background=hiliteColors["background"],
                          foreground=hiliteColors["foreground"])
        text.tag_add("run-highlight", startPos, endPos)
        self.runHighlightCounter += 1
        currentCount = self.runHighlightCounter

        def clearHighlight():
            if self.runHighlightCounter == currentCount:
                text.tag_remove("run-highlight", "1.0", "end")

        text.after(self.HIGHLIGHT_DURATION, clearHighlight)

    def clearRunHighlight(self):
        """Immediately purges visual execution highlights."""
        self.runHighlightCounter += 1   
        self.editwin.text.tag_remove("run-highlight", "1.0", "end")

    def run_selection_event(self, event):
        """Execute specifically highlighted text."""
        if isinstance(self.editwin, outwin.OutputWindow):
            self.editwin.text.bell()
            return 'break'

        text = self.editwin.text
        try:
            sel = text.get("sel.first", "sel.last")
        except TclError:
            text.bell()
            return 'break'

        if not sel.strip():
            text.bell()
            return 'break'

        self.highlightRunCode("sel.first", "sel.last")
        if not self._prepare_for_run():
            return 'break'

        interp = self.shell.interp
        try:
            code = compile(sel, '<selection>', 'exec')
            # self.flist.set_run_indicator(True)
            interp.runcode(code)
        except (SyntaxError, OverflowError, ValueError) as err:
            msg = getattr(err, 'msg', '') or str(err) or "<no detail available>"
            self.errorbox("SyntaxError in Selection", msg)

        self.editwin.text.focus_set()
        return 'break'

    def run_current_line_event(self, event):
        """Execute the single line of code under the cursor."""
        if isinstance(self.editwin, outwin.OutputWindow):
            self.editwin.text.bell()
            return 'break'

        text = self.editwin.text
        current_line = text.index("insert")
        line_start = f"{current_line} linestart"
        line_end = f"{current_line} lineend"
        line_text = text.get(line_start, line_end).strip()

        if not line_text:
            text.bell()
            return 'break'

        self.highlightRunCode(line_start, line_end)
        if not self._prepare_for_run():
            return 'break'

        interp = self.shell.interp
        try:
            code = compile(line_text, '<current line>', 'exec')
            # self.flist.set_run_indicator(True)
            interp.runcode(code)
        except (SyntaxError, OverflowError, ValueError) as err:
            msg = getattr(err, 'msg', '') or str(err) or "<no detail available>"
            self.errorbox("SyntaxError in Current Line", msg)

        self.editwin.text.focus_set()
        return 'break'

    def run_current_paragraph_event(self, event):
        """Execute the localized block of code bounded by empty lines."""
        if isinstance(self.editwin, outwin.OutputWindow):
            self.editwin.text.bell()
            return 'break'

        text = self.editwin.text
        current_pos = text.index("insert")

        para_start = current_pos
        while True:
            line_start = f"{para_start} linestart"
            line_end = f"{para_start} lineend"
            line_text = text.get(line_start, line_end).strip()

            if not line_text or text.compare(line_start, "<=", "1.0"):
                if not line_text:
                    para_start = f"{para_start} +1 line"
                break
            para_start = f"{para_start} -1 line"

        para_end = current_pos
        while True:
            line_start = f"{para_end} linestart"
            line_end = f"{para_end} lineend"
            line_text = text.get(line_start, line_end).strip()

            if not line_text or text.compare(line_end, ">=", "end -1c"):
                if not line_text:
                    para_end = f"{para_end} -1 line"
                break
            para_end = f"{para_end} +1 line"

        para_end = f"{para_end} lineend +1c"
        para_text = text.get(para_start, para_end).strip()

        if not para_text:
            text.bell()
            return 'break'

        self.highlightRunCode(para_start, para_end)
        if not self._prepare_for_run():
            return 'break'

        interp = self.shell.interp
        try:
            code = compile(para_text, '<current paragraph>', 'exec')
            # self.flist.set_run_indicator(True)
            interp.runcode(code)
        except (SyntaxError, OverflowError, ValueError) as err:
            msg = getattr(err, 'msg', '') or str(err) or "<no detail available>"
            self.errorbox("SyntaxError in Current Paragraph", msg)

        self.editwin.text.focus_set()
        return 'break'


if __name__ == "__main__":
    from unittest import main
    main('pem.pem_test.test_runscript', verbosity=2)