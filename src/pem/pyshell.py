#! /usr/bin/env python3
"""The PEM shell window and the GUI side of code execution.

Three layers live here:

  * ``ModifiedInterpreter`` -- owns the execution subprocess.  It spawns and
    connects to it over the RPC socket, keeps a pre-warmed *spare* subprocess
    in the wings so Run is near-instant, restarts/kills the subprocess off the
    Tk thread, and runs the ~15 ms poll loop that pumps RPC responses (and the
    subprocess's stdout/stderr callbacks) back into the GUI.
  * ``PyShell`` -- the interactive Console window (an ``OutputWindow``): the
    ``>>>`` prompt, history, readline, and the *active-sink* routing that sends
    each run's output either here or to an editor tab's output pane.
  * ``main()`` -- builds the Tk root, the file list, and the first window.

The subprocess itself is a separate, near-bare Python process; see
``pem.execution.run``.
"""

import sys
if __name__ == "__main__":
    # Running this file directly (python pyshell.py) -- make "import
    # pem.pyshell" elsewhere resolve to this same module object.
    sys.modules['pem.pyshell'] = sys.modules['__main__']

try:
    from tkinter import *
except ImportError:
    print("** PEM can't import Tkinter.\n"
          "Your Python may not be configured for Tk. **", file=sys.__stderr__)
    raise SystemExit(1)

if sys.platform == 'win32':
    from pem.util import fix_win_hidpi, set_win_app_id
    fix_win_hidpi()
    # Show PEM as its own app in the taskbar instead of grouping under python.
    set_win_app_id('PythonMusic.PEM')

from tkinter import messagebox
from tkinter import simpledialog

from code import InteractiveInterpreter
import itertools
import linecache
import os
import os.path
from platform import python_version
import re
import signal
import socket
import subprocess
from textwrap import TextWrapper
import threading
import time
import tokenize
import warnings

from pem.text.colorizer import ColorDelegator
from pem.config import pemConf
from pem.text.delegator import Delegator
from pem.editing.editor import EditorWindow, fixwordbreaks
from pem.editing.filelist import FileList
from pem.shell.outwin import OutputWindow
from pem import perflog
from pem.searching import replace
from pem.execution import rpc
from pem.execution.run import pem_formatwarning, StdInputFile, StdOutputFile
from pem.text.undo import UndoDelegator

# Default for testing; defaults to True in main() for running.
use_subprocess = False

HOST = '127.0.0.1' # python execution server on localhost loopback
PORT = 0  # someday pass in host, port for remote debug capability

# Marker passed to a frozen build's own executable when it is re-launched as
# the execution subprocess.  Must match PEM.py's SUBPROCESS_FLAG.
SUBPROCESS_FLAG = '--pem-subprocess'

# Make `exit`/`quit` (typed without parens at the shell) say "Use exit() or
# Ctrl-D (end-of-file) to exit".  Absent under `python -S`, where the site
# builtins don't exist.
try:
    eof = 'Ctrl-D (end-of-file)'
    exit.eof = eof
    quit.eof = eof
except NameError:
    pass

# pem_showwarning (installed by capture_warnings() below) writes warnings to
# whatever warning_stream currently points at.  By default that's the real
# stderr; ScriptBinding.checksyntax() temporarily repoints it at the shell
# window so warnings raised while checking the user's code surface there.
warning_stream = sys.__stderr__  # None, at least on Windows, if no console.

def pem_showwarning(
        message, category, filename, lineno, file=None, line=None):
    """A drop-in replacement for warnings.showwarning that renders into PEM.

    Formats with pem_formatwarning, defaults ``file`` to ``warning_stream``,
    appends a ">>> " prompt, and swallows AttributeError/OSError if that stream
    is invalid (e.g. no console attached, as on Windows).
    """
    if file is None:
        file = warning_stream
    try:
        file.write(pem_formatwarning(
                message, category, filename, lineno, line=line))
        file.write(">>> ")
    except (AttributeError, OSError):
        pass  # if file (probably __stderr__) is invalid, skip warning.

_warnings_showwarning = None

def capture_warnings(capture):
    "Replace warning.showwarning with pem_showwarning, or reverse."

    global _warnings_showwarning
    if capture:
        if _warnings_showwarning is None:
            _warnings_showwarning = warnings.showwarning
            warnings.showwarning = pem_showwarning
    else:
        if _warnings_showwarning is not None:
            warnings.showwarning = _warnings_showwarning
            _warnings_showwarning = None

capture_warnings(True)

def extended_linecache_checkcache(filename=None,
                                  orig_checkcache=linecache.checkcache):
    """Extend linecache.checkcache to preserve the <pyshell#...> entries

    Rather than repeating the linecache code, patch it to save the
    <pyshell#...> entries, call the original linecache.checkcache()
    (skipping them), and then restore the saved entries.

    orig_checkcache is bound at definition time to the original
    method, allowing it to be patched.
    """
    cache = linecache.cache
    save = {}
    for key in list(cache):
        if key[:1] + key[-1:] == '<>':
            save[key] = cache.pop(key)
    orig_checkcache(filename)
    cache.update(save)

# Patch linecache.checkcache():
linecache.checkcache = extended_linecache_checkcache


class PyShellEditorWindow(EditorWindow):
    "Regular text edit window in PEM"

    def __init__(self, *args):
        EditorWindow.__init__(self, *args)
        # The Console menu item / toolbar button toggles the Console's
        # visibility rather than only ever opening it.
        self.text.bind("<<open-python-shell>>", self.flist.toggle_shell)
        self.text.bind("<FocusIn>", self._on_focus, add="+")

    def _on_focus(self, event):
        self.flist.last_focused_editor = self

    rmenu_specs = [
        ("Cut", "<<cut>>", "rmenu_check_cut"),
        ("Copy", "<<copy>>", "rmenu_check_copy"),
        ("Paste", "<<paste>>", "rmenu_check_paste"),
    ]


    def _close(self):
        "Extend base method"
        EditorWindow._close(self)


class PyShellFileList(FileList):
    "Extend base class: PEM supports a shell"

    # override FileList's class variable, instances return PyShellEditorWindow
    # instead of EditorWindow when new edit windows are created.
    EditorWindow = PyShellEditorWindow

    pyshell = None
    interp_cwd = None          # tracks interpreter's current working directory
    last_focused_editor = None  # last editor window to receive focus

    def open_shell(self, event=None):
        if self.pyshell:
            self.pyshell.show()
            return self.pyshell

        # Seed interpreter cwd from the focused editor's working directory
        editor = self.last_focused_editor
        if editor is not None:
            if editor.io.filename:
                editor_cwd = os.path.dirname(os.path.abspath(editor.io.filename))
            elif editor.io.dirname:
                editor_cwd = editor.io.dirname
            else:
                editor_cwd = None
            if editor_cwd:
                self.interp_cwd = editor_cwd
        self.pyshell = PyShell(self)
        if self.pyshell:
            if not self.pyshell.begin():
                return None
            self.pyshell.show()
        return self.pyshell

    def toggle_shell(self, event=None):
        """Bound to <<open-python-shell>>. Hides the console if visible, shows it otherwise.

        On macOS, deiconify() triggers a FocusIn storm on the editor hierarchy that
        transiently raises the editor above the console.  Querying live window state
        (e.g. wm stackorder) during this window produces wrong show/hide decisions.
        _desired_visible tracks intent instead — it is set by show() and cleared here
        — so the toggle always acts on what the user last requested, not on the
        current unstable z-order.

        TODO: The console still briefly dips behind the editor after deiconify.
        Fixing this robustly likely requires a native macOS hook that prevents the
        editor from being raised during the console's activation sequence.
        """
        shell = self.pyshell
        state = None
        if shell and hasattr(shell, 'top') and shell.top.winfo_exists():
            try:
                state = shell.top.state()
            except TclError:
                pass
        if state == 'normal' and getattr(shell, '_desired_visible', False):
            # Console was intentionally shown — hide it.
            self.hide_shell()
            return shell
        return self.open_shell(event)

    def hide_shell(self):
        """Hide the Console, preserving its text and history.

        The Console is always open while PEM runs; closing its window (by any
        means) only hides it.  Its state is cleared solely by the Console's own
        Reset button or by quitting PEM.  Hiding never affects a running
        program -- it keeps executing in the background.
        """
        shell = self.pyshell
        if shell is None:
            return
        if not (hasattr(shell, 'top') and shell.top.winfo_exists()):
            return
        shell._desired_visible = False
        # Transfer focus to the editor before hiding so macOS doesn't briefly
        # flash the Console as it searches for the next key window.
        try:
            if self.last_focused_editor and self.last_focused_editor.text:
                self.last_focused_editor.text.focus_set()
        except Exception:
            pass
        shell.top.withdraw()

    def close_all_callback(self, *args, **kwds):
        """Exit PEM.

        The editor window is PEM's canonical window, so closing it -- or
        choosing Quit / Close All -- shuts everything down, including the
        always-open Console and its execution subprocess.

        Checks run before anything is torn down, so the user can still cancel:
        a running program prompts for confirmation, then each unsaved editor
        tab prompts to save.  Once teardown begins it always completes.
        """
        if getattr(self, '_exiting', False):
            return "break"

        # --- Check phase (cancelable; nothing has been torn down yet). ---
        shell = self.pyshell
        if shell is not None and getattr(shell, 'executing', False):
            if not messagebox.askokcancel(
                    "Kill?",
                    "Your program is still running!\n Do you want to kill it?",
                    default="ok", parent=shell.text):
                return "break"

        editors = [e for e in self.inversedict
                   if not getattr(e, 'is_shell', False)]
        for editor in editors:
            if str(editor.maybesave()) == "cancel":
                return "break"

        # --- Teardown phase (no further cancellation). ---
        # Defer the actual window/Console teardown to an idle callback. When the
        # exit is triggered from the menu bar (File > Close, or Quit), this lets
        # macOS finish dismissing the open menu before we destroy the
        # menu-bearing window. Destroying it mid-dismissal is harmless but makes
        # AppKit log a noisy "[NSMenu] Inconsistent state" warning.
        self._exiting = True

        def _teardown():
            for editor in editors:
                editor._close()        # saves were handled above; just tear down
            if shell is not None:
                shell._close()         # kills the subprocess and destroys the Console
            self.root.quit()

        self.root.after_idle(_teardown)
        return "break"


class ModifiedColorDelegator(ColorDelegator):
    "Extend base class: colorizer for the shell window itself"
    def recolorize_main(self):
        self.tag_remove("TODO", "1.0", "iomark")
        self.tag_add("SYNC", "1.0", "iomark")
        ColorDelegator.recolorize_main(self)

    def removecolors(self):
        # Don't remove shell color tags before "iomark"
        for tag in self.tagdefs:
            self.tag_remove(tag, "iomark", "end")


class ModifiedUndoDelegator(UndoDelegator):
    "Extend base class: forbid insert/delete before the I/O mark"
    def insert(self, index, chars, tags=None):
        try:
            if self.delegate.compare(index, "<", "iomark"):
                self.delegate.bell()
                return
        except TclError:
            pass
        UndoDelegator.insert(self, index, chars, tags)

    def delete(self, index1, index2=None):
        try:
            if self.delegate.compare(index1, "<", "iomark"):
                self.delegate.bell()
                return
        except TclError:
            pass
        UndoDelegator.delete(self, index1, index2)

    def undo_event(self, event):
        # Temporarily monkey-patch the delegate's .insert() method to
        # always use the "stdin" tag.  This is needed for undo-ing
        # deletions to preserve the "stdin" tag, because UndoDelegator
        # doesn't preserve tags for deleted text.
        orig_insert = self.delegate.insert
        self.delegate.insert = \
            lambda index, chars: orig_insert(index, chars, "stdin")
        try:
            super().undo_event(event)
        finally:
            self.delegate.insert = orig_insert


class UserInputTaggingDelegator(Delegator):
    """Delegator used to tag user input with "stdin"."""
    def insert(self, index, chars, tags=None):
        if tags is None:
            tags = "stdin"
        self.delegate.insert(index, chars, tags)


class MyRPCClient(rpc.RPCClient):
    "RPCClient that turns a dropped connection into an EOFError for poll_subprocess to catch."

    def handle_EOF(self):
        "Override the base class - just re-raise EOFError"
        raise EOFError


# --- Execution-subprocess process helpers (used on the Tk thread and on
#     background daemon threads, so they take their arguments explicitly and
#     never touch interpreter instance state) -------------------------------

def _spawn_exec_subprocess(arglist):
    """Popen an execution subprocess.

    On macOS the child gets its own process group (and PYTHONUNBUFFERED) so the
    whole group -- including a PythonMusic Qt renderer child -- can be
    reaped together later via os.killpg.
    """
    if sys.platform == 'darwin':
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'
        return subprocess.Popen(arglist, env=env, preexec_fn=os.setpgrp)
    return subprocess.Popen(arglist)


def _terminate_proc(proc):
    """Force-terminate an execution subprocess and its process group.

    The group kill reaps any PythonMusic renderer child that a force-killed
    user process couldn't shut down cleanly.  Safe to call from a daemon thread
    and safe if the process has already exited.
    """
    if not proc:
        return
    try:
        if sys.platform == 'darwin':
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except (OSError, ProcessLookupError):
                pass
        elif sys.platform == 'win32':
            try:
                # CREATE_NO_WINDOW so taskkill (a console app) doesn't flash a
                # black console window each time we reap a subprocess.
                subprocess.run(['taskkill', '/F', '/T', '/PID', str(proc.pid)],
                               capture_output=True,
                               creationflags=subprocess.CREATE_NO_WINDOW)
            except OSError:
                pass
        proc.kill()
    except (OSError, ProcessLookupError):
        return
    else:
        try:
            proc.wait(timeout=1)
        except (OSError, subprocess.TimeoutExpired):
            try:
                proc.kill()
            except (OSError, ProcessLookupError):
                pass
            try:
                proc.wait(timeout=2)
            except (OSError, subprocess.TimeoutExpired):
                pass


def _terminate_conn(clt, proc):
    "Close an RPC connection + its listening socket, then terminate the subprocess."
    if clt is not None:
        try:
            clt.close()
        except Exception:
            pass
        try:
            clt.listening_sock.close()
        except Exception:
            pass
    _terminate_proc(proc)


class _Spare:
    "A pre-built, idle execution subprocess waiting to be promoted to active."
    __slots__ = ('clt', 'proc')

    def __init__(self, clt, proc):
        self.clt = clt
        self.proc = proc


class ModifiedInterpreter(InteractiveInterpreter):
    """GUI-side controller for the execution subprocess.

    Compiles shell input here (via ``code.InteractiveInterpreter``) but runs it
    in a separate process, reached over the RPC socket in ``pem.execution.rpc``.
    Responsibilities: spawn/connect (``start_subprocess``), keep a pre-warmed
    ``_spare`` ready and promote it on restart (``restart_subprocess``), tear the
    old process down off the Tk thread, and pump RPC responses + the subprocess's
    output callbacks back into the shell on a timer (``poll_subprocess``).
    """

    def __init__(self, tkconsole):
        self.tkconsole = tkconsole
        locals = sys.modules['__main__'].__dict__
        InteractiveInterpreter.__init__(self, locals=locals)
        self.restarting = False
        self.port = PORT
        self.original_compiler_flags = self.compile.compiler.flags

    _afterid = None
    rpcclt = None
    rpcsubproc = None
    _spare = None            # a _Spare: pre-built idle subprocess (or None)
    _spare_building = False  # True while a _build_spare daemon thread is in flight
    _closing = False         # set by kill_subprocess; tells in-flight builds to discard

    def spawn_subprocess(self):
        # Builds the arglist fresh each time -- it embeds self.port, which changes
        # when a warm spare (with its own listening socket) is promoted to active.
        perflog.mark("spawn_subprocess: about to Popen execution subprocess")
        self.rpcsubproc = _spawn_exec_subprocess(self.build_subprocess_arglist())
        perflog.mark(f"spawn_subprocess: Popen returned (child pid={self.rpcsubproc.pid})")

    def build_subprocess_arglist(self, port=None):
        """argv for spawning an execution subprocess that connects back to our
        listening socket on ``port``.

        Frozen build: re-launch the bundled executable with SUBPROCESS_FLAG --
        PyInstaller's _MEIPASS2 mechanism makes it reuse the parent's already-
        extracted runtime, so this is fast (no re-extraction).
        From source / an installed pem: spawn ``python -c <bootstrap>``
        that puts the directory containing the ``pem`` package on sys.path
        and runs pem.execution.run.main().
        """
        port = port if port is not None else self.port
        assert port != 0, "Socket should have been assigned a port number."
        warnopts = ['-W' + s for s in sys.warnoptions]
        if getattr(sys, 'frozen', False):
            return [sys.executable, SUBPROCESS_FLAG, str(port)]
        # __file__ here is .../pem/pyshell.py -> grandparent is the dir
        # that contains the 'pem' package (already on sys.path if
        # pem is installed; needed when running from source).
        pkg_parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        bootstrap = (f"import sys; sys.path.insert(0, {pkg_parent!r}); "
                     f"from pem.execution.run import main; main()")
        return [sys.executable] + warnopts + ["-c", bootstrap, str(port)]

    def start_subprocess(self):
        perflog.mark("start_subprocess: begin (acquiring listening socket)")
        addr = (HOST, self.port)
        # Bind the listening socket the subprocess will connect back to.  With
        # PORT == 0 the OS hands us a free ephemeral port, so this normally
        # succeeds on the first try; the short retry is just a safety net.
        for attempt in range(6):
            try:
                self.rpcclt = MyRPCClient(addr)
                break
            except OSError:
                time.sleep(0.05)
        else:
            self.display_port_binding_error()
            return None
        # if PORT was 0, system will assign an 'ephemeral' port. Find it out:
        self.port = self.rpcclt.listening_sock.getsockname()[1]
        # if PORT was not 0, probably working with a remote execution server
        if PORT != 0:
            # To allow reconnection within the 2MSL wait (cf. Stevens TCP
            # V1, 18.6),  set SO_REUSEADDR.  Note that this can be problematic
            # on Windows since the implementation allows two active sockets on
            # the same address!
            self.rpcclt.listening_sock.setsockopt(socket.SOL_SOCKET,
                                           socket.SO_REUSEADDR, 1)
        self.spawn_subprocess()
        #time.sleep(20) # test to simulate GUI not accepting connection
        # Accept the connection from the Python execution server
        self.rpcclt.listening_sock.settimeout(10)
        try:
            self.rpcclt.accept()
        except TimeoutError:
            self.display_no_subprocess_error()
            return None
        perflog.mark("start_subprocess: subprocess connected back over socket")
        self.rpcclt.register("console", self.tkconsole)
        self.rpcclt.register("stdin", self.tkconsole.stdin)
        self.rpcclt.register("stdout", self.tkconsole.stdout)
        self.rpcclt.register("stderr", self.tkconsole.stderr)
        self.rpcclt.register("flist", self.tkconsole.flist)
        self.rpcclt.register("linecache", linecache)
        self.rpcclt.register("interp", self)
        self.transfer_path(with_cwd=True)
        # Apply the desired initial working directory in the subprocess
        target_cwd = self.tkconsole.flist.interp_cwd
        if target_cwd and os.path.isdir(target_cwd):
            self.runcommand(f"import os as _os; _os.chdir({target_cwd!r}); del _os\n")
        self.poll_subprocess()
        # Start warming a spare so the first Run doesn't pay spawn+connect.
        self._start_spare_build()
        perflog.mark("start_subprocess: done (path/cwd transferred, polling started)")
        return self.rpcclt

    # --- Pre-warm pool ------------------------------------------------------
    # A "spare" is a fully-built, idle execution subprocess (own listening
    # socket + connection + sys.path already transferred) sitting in the wings.
    # restart_subprocess() promotes it instantly instead of spawning+connecting
    # on the Tk thread.  Spares are built on a daemon thread; if anything goes
    # wrong, restart_subprocess() falls back to the synchronous path.

    def _start_spare_build(self):
        "Kick off building the next warm spare on a background thread, if needed."
        if self._closing or self._spare is not None or self._spare_building:
            return
        self._spare_building = True
        threading.Thread(target=self._build_spare,
                         name='PemSpareBuilder', daemon=True).start()

    def _build_spare(self):
        "Daemon-thread worker: spawn + connect + transfer sys.path for one spare."
        clt = proc = None
        try:
            if self._closing:
                return
            perflog.mark("_build_spare: begin (background)")
            clt = MyRPCClient((HOST, 0))                       # own ephemeral port
            port = clt.listening_sock.getsockname()[1]
            arglist = self.build_subprocess_arglist(port=port)
            proc = _spawn_exec_subprocess(arglist)
            clt.listening_sock.settimeout(15)
            clt.accept()
            # Register the GUI-side callback objects (same set as start_subprocess()).
            clt.register("console", self.tkconsole)
            clt.register("stdin", self.tkconsole.stdin)
            clt.register("stdout", self.tkconsole.stdout)
            clt.register("stderr", self.tkconsole.stderr)
            clt.register("flist", self.tkconsole.flist)
            clt.register("linecache", linecache)
            clt.register("interp", self)
            # Pre-transfer sys.path (with cwd, like start_subprocess) and the
            # current interpreter cwd, fire-and-forget: RPC requests are handled
            # in order, so this lands before any later runcode on this connection.
            path = [''] + list(sys.path)
            clt.asyncqueue("exec", "runcode",
                ("if 1:\n    import sys as _sys\n    _sys.path = %r\n    del _sys\n" % (path,),), {})
            target_cwd = getattr(self.tkconsole.flist, 'interp_cwd', None)
            if target_cwd and os.path.isdir(target_cwd):
                clt.asyncqueue("exec", "runcode",
                    ("import os as _os; _os.chdir(%r); del _os\n" % (target_cwd,),), {})
            if self._closing:
                raise RuntimeError("PEM closing")
            self._spare = _Spare(clt, proc)
            perflog.mark(f"_build_spare: ready (spare pid={proc.pid})")
        except BaseException as why:
            perflog.mark(f"_build_spare: failed ({type(why).__name__}: {why})")
            _terminate_conn(clt, proc)
            self._spare = None
        finally:
            self._spare_building = False

    def restart_subprocess(self, with_cwd=False, filename=''):
        if self.restarting:
            return self.rpcclt
        perflog.mark("restart_subprocess: begin")
        self.restarting = True
        console = self.tkconsole
        # Drop any pending buffered writes from the dying subprocess and cancel
        # the pending flush, so a late-arriving \r-overwrite can't land in the
        # console after the restart cleanup has trimmed iomark -- which would
        # leave stale chars past iomark and make the next typed command look
        # syntactically incomplete (the `...` continuation symptom).
        flush_id = getattr(console, '_write_flush_id', None)
        if flush_id is not None:
            try:
                console.text.after_cancel(flush_id)
            except Exception:
                pass
        console._write_flush_id = None
        console._write_buffer = []
        was_executing = console.executing
        console.executing = False
        # try:
        #     console.flist.set_run_indicator(False)
        # except Exception:
        #     pass
        self.active_seq = None

        old_clt = self.rpcclt
        old_proc = self.rpcsubproc
        spare = self._spare

        if spare is not None:
            # Fast path: promote the pre-built idle subprocess.  No spawn / no
            # connect / no path transfer on the Tk thread.
            perflog.mark(f"restart_subprocess: promoting warm spare (pid={spare.proc.pid})")
            self._spare = None
            self.rpcclt = spare.clt
            self.rpcsubproc = spare.proc
            # The spare's MyRPCClient was accepted on the spare-builder daemon
            # thread, so rpc.SocketIO.sockthread points there.  Re-point it at
            # the thread that now owns/polls this connection (the Tk thread),
            # otherwise getresponse() takes its cross-thread Condition-wait path
            # and deadlocks (the notifying poll loop never runs on the dead
            # builder thread).
            self.rpcclt.sockthread = threading.current_thread()
            # The spare has its own listening socket on its own port; keep
            # self.port in sync so a later slow-path spawn_subprocess() (if a
            # future spare build fails) targets the right port.
            try:
                self.port = self.rpcclt.listening_sock.getsockname()[1]
            except Exception:
                pass
            # Tear down the old connection + subprocess off the Tk thread
            # (the killpg/taskkill is the slow part on Windows).
            threading.Thread(target=_terminate_conn, args=(old_clt, old_proc),
                             name='PemTerminator', daemon=True).start()
            if with_cwd:
                # Manual restart (Ctrl-F6 / Stop): cwd resets to the process cwd.
                cwd = os.getcwd()
                self.tkconsole.flist.interp_cwd = cwd
                try:
                    self.rpcclt.asyncqueue("exec", "runcode",
                        ("import os as _os; _os.chdir(%r); del _os\n" % (cwd,),), {})
                except Exception:
                    pass
            perflog.mark("restart_subprocess: spare promoted")
        else:
            # Slow path: no spare ready -> kill old + spawn + connect (synchronous).
            perflog.mark("restart_subprocess: no warm spare; spawning synchronously")
            try:
                self.rpcclt.close()             # give the old subprocess EOF (fast)
            except Exception:
                pass
            threading.Thread(target=_terminate_proc, args=(old_proc,),
                             name='PemTerminator', daemon=True).start()
            self.spawn_subprocess()
            try:
                self.rpcclt.accept()
            except TimeoutError:
                self.display_no_subprocess_error()
                self.restarting = False
                return None
            perflog.mark("restart_subprocess: new subprocess connected back")
            self.transfer_path(with_cwd=with_cwd)
            if with_cwd:
                self.tkconsole.flist.interp_cwd = os.getcwd()

        console.stop_readline()
        # annotate restart in shell window and mark it
        console.text.delete("iomark", "end-1c")
        console.text.mark_set("restart", "end-1c")
        console.text.mark_gravity("restart", "left")
        # Visible banner in the Console for every restart of the execution
        # subprocess -- script Run (filename = the script's path) and manual
        # restart (Stop / Ctrl-F6, filename = '').  write_to_console() bypasses
        # the active-sink dispatch so the banner always lands in the Console
        # rather than a script's target output pane.
        label = f"Running '{os.path.splitext(os.path.basename(filename))[0]}'" if filename else "Reinitializing"
        console.write_to_console(f"\n======= {label} =======\n", "stdout")
        if not filename:
            # Manual restart (Stop / Ctrl-F6): nothing's running, so the
            # interactive prompt -- and subsequent Console output -- belongs in
            # the Console.  (A script Run keeps the editor sink set by
            # _prepare_for_run; we mustn't disturb that here.)
            console.set_active_sink(None)
            console.showprompt()

        self.compile.compiler.flags = self.original_compiler_flags
        self.restarting = False
        # Warm the next spare in the background.
        self._start_spare_build()
        perflog.mark("restart_subprocess: done")
        return self.rpcclt

    def __request_interrupt(self):
        self.rpcclt.remotecall("exec", "interrupt_the_server", (), {})

    def interrupt_subprocess(self):
        threading.Thread(target=self.__request_interrupt).start()

    def kill_subprocess(self):
        self._closing = True   # tell any in-flight spare build to discard itself
        if self._afterid is not None:
            self.tkconsole.text.after_cancel(self._afterid)
        try:
            self.rpcclt.listening_sock.close()
        except AttributeError:  # no socket
            pass
        try:
            self.rpcclt.close()
        except AttributeError:  # no socket
            pass
        self.terminate_subprocess()
        self.tkconsole.executing = False
        self.rpcclt = None

    def terminate_subprocess(self):
        "Force-terminate the active subprocess and any pre-built spare."
        _terminate_proc(self.rpcsubproc)
        spare = self._spare
        if spare is not None:
            self._spare = None
            _terminate_conn(spare.clt, spare.proc)

    def transfer_path(self, with_cwd=False):
        if with_cwd:        # Issue 13506
            path = ['']     # include Current Working Directory
            path.extend(sys.path)
        else:
            path = sys.path

        self.runcommand("""if 1:
        import sys as _sys
        _sys.path = {!r}
        del _sys
        \n""".format(path))

    active_seq = None

    def poll_subprocess(self):
        clt = self.rpcclt
        if clt is None:
            return
        try:
            # Short wait + a cap on how many incoming console.write callbacks
            # we'll service in one pass, so a script flooding output can't
            # monopolise the Tk event loop (it stays responsive; output flows
            # in small batches via the poll reschedule below).  The cap is
            # generous because PyShell.write only appends to a buffer now --
            # actual rendering is deferred to the 16ms _flush_writes tick --
            # so each serviced request is microseconds rather than ms.
            response = clt.pollresponse(self.active_seq, wait=0.002, maxrequests=64)
        except (EOFError, OSError, KeyboardInterrupt) as why:
            # lost connection or subprocess terminated itself, restart
            # [the KBI is from rpc.SocketIO.handle_EOF()]
            if self.tkconsole.closing:
                return
            perflog.mark(f"poll_subprocess: lost connection to subprocess ({type(why).__name__}) -> auto-restarting")
            response = None
            self.active_seq = None
            if self.tkconsole.executing:
                self.tkconsole.executing = False
            self.restart_subprocess()
        if response:
            perflog.mark(f"poll_subprocess: got response from subprocess ({response[0]!r})")
            self.tkconsole.resetoutput()
            self.active_seq = None
            how, what = response
            console = self.tkconsole.console
            if how == "OK":
                if what is not None:
                    print(repr(what), file=console)
            elif how == "EXCEPTION":
                pass
            elif how == "ERROR":
                errmsg = "pyshell.ModifiedInterpreter: Subprocess ERROR:\n"
                print(errmsg, what, file=sys.__stderr__)
                print(errmsg, what, file=console)
            # we received a response to the currently active seq number:
            try:
                self.tkconsole.endexecuting()
            except AttributeError:  # shell may have closed
                pass
            perflog.mark("poll_subprocess: endexecuting() returned; rescheduling poll")
        # Reschedule myself
        if not self.tkconsole.closing:
            self._afterid = self.tkconsole.text.after(
                self.tkconsole.pollinterval, self.poll_subprocess)

    gid = 0

    def execsource(self, source):
        "Like runsource() but assumes complete exec source"
        filename = self.stuffsource(source)
        self.execfile(filename, source)

    def execfile(self, filename, source=None):
        "Execute an existing file"
        if source is None:
            with tokenize.open(filename) as fp:
                source = fp.read()
                if use_subprocess:
                    source = (f"__file__ = r'''{os.path.abspath(filename)}'''\n"
                              + source + "\ndel __file__")
        try:
            code = compile(source, filename, "exec")
        except (OverflowError, SyntaxError):
            self.tkconsole.resetoutput()
            print('*** Error in script or command!\n'
                 'Traceback (most recent call last):',
                  file=self.tkconsole.stderr)
            InteractiveInterpreter.showsyntaxerror(self, filename)
            self.tkconsole.showprompt()
        else:
            self.runcode(code)

    def runsource(self, source):
        "Extend base class method: Stuff the source in the line cache first"
        filename = self.stuffsource(source)
        # at the moment, InteractiveInterpreter expects str
        assert isinstance(source, str)
        # InteractiveInterpreter.runsource() calls its runcode() method,
        # which is overridden (see below)
        return InteractiveInterpreter.runsource(self, source, filename)

    def stuffsource(self, source):
        "Stuff source in the filename cache"
        filename = "<pyshell#%d>" % self.gid
        self.gid = self.gid + 1
        lines = source.split("\n")
        linecache.cache[filename] = len(source)+1, 0, lines, filename
        return filename

    def prepend_syspath(self, filename):
        "Prepend sys.path with file's directory if not already included"
        self.runcommand("""if 1:
            _filename = {!r}
            import sys as _sys
            from os.path import dirname as _dirname
            _dir = _dirname(_filename)
            if not _dir in _sys.path:
                _sys.path.insert(0, _dir)
            del _filename, _sys, _dirname, _dir
            \n""".format(filename))

    def showsyntaxerror(self, filename=None, **kwargs):
        """Override Interactive Interpreter method: Use Colorizing

        Color the offending position instead of printing it and pointing at it
        with a caret.

        """
        tkconsole = self.tkconsole
        text = tkconsole.text
        text.tag_remove("ERROR", "1.0", "end")
        type, value, tb = sys.exc_info()
        msg = getattr(value, 'msg', '') or value or "<no detail available>"
        lineno = getattr(value, 'lineno', '') or 1
        offset = getattr(value, 'offset', '') or 0
        if offset == 0:
            lineno += 1 #mark end of offending line
        if lineno == 1:
            pos = "iomark + %d chars" % (offset-1)
        else:
            pos = "iomark linestart + %d lines + %d chars" % \
                  (lineno-1, offset-1)
        tkconsole.colorize_syntax_error(text, pos)
        tkconsole.resetoutput()
        self.write("SyntaxError: %s\n" % msg)
        tkconsole.showprompt()

    def showtraceback(self):
        "Extend base class method to reset output properly"
        self.tkconsole.resetoutput()
        self.checklinecache()
        InteractiveInterpreter.showtraceback(self)

    def checklinecache(self):
        "Remove keys other than '<pyshell#n>'."
        cache = linecache.cache
        for key in list(cache):  # Iterate list because mutate cache.
            if key[:1] + key[-1:] != "<>":
                del cache[key]

    def runcommand(self, code):
        "Run code in the subprocess for its side effects only (no echoed result)."
        # The code better not raise an exception!
        if self.tkconsole.executing:
            self.display_executing_dialog()
            return 0
        if self.rpcclt:
            self.rpcclt.remotequeue("exec", "runcode", (code,), {})
        else:
            exec(code, self.locals)
        return 1

    def runcode(self, code):
        "Override base class method"
        if self.tkconsole.executing:
            perflog.mark("ModifiedInterpreter.runcode: called while still executing")
            # If executing is True but we're trying to run new code, check if
            # the subprocess is actually responding. If not, reset state.
            if self.rpcclt is not None and self.active_seq is not None:
               # Check if subprocess is still responding
               try:
                  # Try to poll for response with short timeout
                  response = self.rpcclt.pollresponse(self.active_seq, wait=0.01, maxrequests=4)
                  if response is None:
                     # No response yet, subprocess might be stuck - restart it
                     perflog.mark("ModifiedInterpreter.runcode: prior run unresponsive -> restarting subprocess")
                     self.restart_subprocess()
               except (EOFError, OSError):
                  # Connection broken, restart subprocess
                  perflog.mark("ModifiedInterpreter.runcode: prior run's connection broken -> restarting subprocess")
                  self.restart_subprocess()
            else:
               # No active sequence but executing is True - reset state
               self.tkconsole.executing = False
               self.active_seq = None
        self.checklinecache()
        try:
            self.tkconsole.beginexecuting()
            if self.rpcclt is not None:
                self.active_seq = self.rpcclt.asyncqueue("exec", "runcode",
                                                        (code,), {})
                perflog.mark(f"ModifiedInterpreter.runcode: queued runcode RPC (seq={self.active_seq})")
            else:
                exec(code, self.locals)
        except SystemExit:
            if not self.tkconsole.closing:
                if messagebox.askyesno(
                    "Exit?",
                    "Do you want to exit altogether?",
                    default="yes",
                    parent=self.tkconsole.text):
                    raise
                else:
                    self.showtraceback()
            else:
                raise
        except:
            if use_subprocess:
                print("PEM internal error in runcode()",
                      file=self.tkconsole.stderr)
                self.showtraceback()
                self.tkconsole.endexecuting()
            else:
                if self.tkconsole.canceled:
                    self.tkconsole.canceled = False
                    print("KeyboardInterrupt", file=self.tkconsole.stderr)
                else:
                    self.showtraceback()
        finally:
            if not use_subprocess:
                try:
                    self.tkconsole.endexecuting()
                except AttributeError:  # shell may have closed
                    pass

    def write(self, s):
        "Override base class method"
        return self.tkconsole.stderr.write(s)

    def display_port_binding_error(self):
        messagebox.showerror(
            "Port Binding Error",
            "PEM can't bind to a TCP/IP port, which is necessary to "
            "communicate with its Python execution server.  This might be "
            "because no networking is installed on this computer.  "
            "Run PEM with the -n command line switch to start without a "
            "subprocess and refer to Help/PEM Help 'Running without a "
            "subprocess' for further details.",
            parent=self.tkconsole.text)

    def display_no_subprocess_error(self):
        messagebox.showerror(
            "Subprocess Connection Error",
            "PEM's subprocess didn't make connection.\n"
            "See the 'Startup failure' section of the PEM doc, online at\n"
            "https://docs.python.org/3/library/pem.html#startup-failure",
            parent=self.tkconsole.text)

    def display_executing_dialog(self):
        messagebox.showerror(
            "Already executing",
            "The Python Console window is already executing a command; "
            "please wait until it is finished.",
            parent=self.tkconsole.text)


class PyShell(OutputWindow):
    """The interactive Console window: prompt, history, readline, and output routing.

    Owns a ModifiedInterpreter (and thus the execution subprocess).  Per-run
    output is dispatched by ``active_sink``: a script Run points it at that
    editor tab's output pane, Console-entered code points it back here (None).
    """
    from pem.shell.squeezer import Squeezer

    shell_title = "PEM Console"

    # Override classes
    ColorDelegator = ModifiedColorDelegator
    UndoDelegator = ModifiedUndoDelegator

    # Override menus
    menu_specs = [
        # ("shell", "_Console"),
        ("window", "_Window"),
        ("help", "_Help"),
    ]

    # Extend right-click context menu
    rmenu_specs = OutputWindow.rmenu_specs + [
        ("Squeeze", "<<squeeze-current-text>>"),
    ]
    _idx = 1 + len(list(itertools.takewhile(
        lambda rmenu_item: rmenu_item[0] != "Copy", rmenu_specs)
    ))
    rmenu_specs.insert(_idx, ("Copy with prompts",
                              "<<copy-with-prompts>>",
                              "rmenu_check_copy"))
    del _idx

    allow_line_numbers = False
    allow_highlight_current_line = True
    user_input_insert_tags = "stdin"

    # New classes
    from pem.shell.history import History
    from pem.shell.sidebar import ShellSidebar

    def __init__(self, flist=None):
        self.interp = ModifiedInterpreter(self)
        if flist is None:
            root = Tk()
            fixwordbreaks(root)
            root.withdraw()
            flist = PyShellFileList(root)

        self.shell_sidebar = None  # initialized below
        self._desired_visible = False

        OutputWindow.__init__(self, flist, None, None)

        self.usetabs = False
        # indentwidth must be 8 when using tabs.  See note in EditorWindow:
        self.indentwidth = 4

        self.sys_ps1 = sys.ps1 if hasattr(sys, 'ps1') else '>>>\n'
        self.prompt_last_line = self.sys_ps1.split('\n')[-1]
        self.prompt = self.sys_ps1  # Changes when debug active

        text = self.text
        text.configure(wrap="char")
        text.bind("<<newline-and-indent>>", self.enter_callback)
        text.bind("<<plain-newline-and-indent>>", self.linefeed_callback)
        text.bind("<<interrupt-execution>>", self.cancel_callback)
        text.bind("<<end-of-file>>", self.eof_callback)
        text.bind("<<copy-with-prompts>>", self.copy_with_prompts_callback)
        text.bind("<Key-Up>", self.up_arrow_callback)
        text.bind("<Key-Down>", self.down_arrow_callback)
        if use_subprocess:
            text.bind("<<view-restart>>", self.view_restart_mark)
            text.bind("<<restart-shell>>", self.restart_shell)
        self.squeezer = self.Squeezer(self)
        text.bind("<<squeeze-current-text>>",
                  self.squeeze_current_text_event)

        self.save_stdout = sys.stdout
        self.save_stderr = sys.stderr
        self.save_stdin = sys.stdin
        from pem.editing import iomenu
        self.stdin = StdInputFile(self, "stdin",
                                  iomenu.encoding, iomenu.errors)
        self.stdout = StdOutputFile(self, "stdout",
                                    iomenu.encoding, iomenu.errors)
        self.stderr = StdOutputFile(self, "stderr",
                                    iomenu.encoding, "backslashreplace")
        self.console = StdOutputFile(self, "console",
                                     iomenu.encoding, iomenu.errors)
        if not use_subprocess:
            sys.stdout = self.stdout
            sys.stderr = self.stderr
            sys.stdin = self.stdin
        try:
            # page help() text to shell.
            import pydoc # import must be done here to capture i/o rebinding.
            # XXX KBK 27Dec07 use text viewer someday, but must work w/o subproc
            pydoc.pager = pydoc.plainpager
        except:
            sys.stderr = sys.__stderr__
            raise
        #
        self.history = self.History(self.text)
        #
        self.pollinterval = 15  # millisec between subprocess poll cycles

        self.shell_sidebar = self.ShellSidebar(self)

        # Insert UserInputTaggingDelegator at the top of the percolator,
        # but make calls to text.insert() skip it.  This causes only insert
        # events generated in Tcl/Tk to go through this delegator.
        self.text.insert = self.per.top.insert
        self.per.insertfilter(UserInputTaggingDelegator())

    def ResetFont(self):
        super().ResetFont()

        if self.shell_sidebar is not None:
            self.shell_sidebar.update_font()

    def ResetColorizer(self):
        super().ResetColorizer()

        theme = pemConf.CurrentTheme()
        tag_colors = {
          "stdin": {'background': None, 'foreground': None},
          "stdout": pemConf.GetHighlight(theme, "stdout"),
          "stderr": pemConf.GetHighlight(theme, "stderr"),
          "console": pemConf.GetHighlight(theme, "normal"),
        }
        for tag, tag_colors_config in tag_colors.items():
            self.text.tag_configure(tag, **tag_colors_config)
            
        # The Console gives the current line a pale-yellow highlight and the
        # mouse selection a blue one, with the selection drawn on top.
        self.text.tag_configure("current-line", background="#ffffaa")
        self.text.tag_configure("sel", background="#add6ff")
        self.text.tag_lower("current-line", "sel")

        if self.shell_sidebar is not None:
            self.shell_sidebar.update_colors()

    def set_line_and_column(self, event=None):
        "Update the status bar, keeping the current-line highlight in step with it."
        super().set_line_and_column(event)
        self._highlight_current_line()


    def _highlight_current_line(self, event=None):
        "Move the 'current-line' highlight tag onto the line the cursor is on."
        if getattr(self, 'text', None) is None or getattr(self, 'closing', False):
            return  # widget already gone (teardown)
        try:
            # Clear it everywhere first: the Console inserts output and prompts
            # programmatically, which can leave the tag on stale ranges.
            self.text.tag_remove("current-line", "1.0", "end")
            line = self.text.index("insert").split('.')[0]
            self.text.tag_add("current-line", f"{line}.0", f"{line}.end+1c")
        except (AttributeError, TclError):
            pass  # widget vanished mid-teardown


    def replace_event(self, event):
        replace.replace(self.text, insert_tags="stdin")
        return "break"

    def get_standard_extension_names(self):
        return pemConf.GetExtensions(shell_only=True)

    def get_prompt_text(self, first, last):
        """Return text between first and last with prompts added."""
        text = self.text.get(first, last)
        lineno_range = range(
            int(float(first)),
            int(float(last))
         )
        prompts = [
            self.shell_sidebar.line_prompts.get(lineno)
            for lineno in lineno_range
        ]
        return "\n".join(
            line if prompt is None else f"{prompt} {line}"
            for prompt, line in zip(prompts, text.splitlines())
        ) + "\n"


    def copy_with_prompts_callback(self, event=None):
        """Copy selected lines to the clipboard, with prompts.

        This makes the copied text useful for doc-tests and interactive
        shell code examples.

        This always copies entire lines, even if only part of the first
        and/or last lines is selected.
        """
        text = self.text
        selfirst = text.index('sel.first linestart')
        if selfirst is None:  # Should not be possible.
            return  # No selection, do nothing.
        sellast = text.index('sel.last')
        if sellast[-1] != '0':
            sellast = text.index("sel.last+1line linestart")
        text.clipboard_clear()
        prompt_text = self.get_prompt_text(selfirst, sellast)
        text.clipboard_append(prompt_text)

    reading = False
    executing = False
    canceled = False
    endoffile = False
    closing = False
    _stop_readline_flag = False

    # --- Script-output routing ----------------------------------------------
    # active_sink is the destination for subprocess output (script print() and
    # input()).  Callers set it explicitly per execution: a runscript Run sets
    # it to that tab's EditorWindow; runit() (Console-entered code) sets it
    # back to None.  None means "write to this Console window."  No automatic
    # clearing on focus changes -- the sink is whatever the most recent
    # execution dispatcher set it to.
    active_sink = None
    # Tail of stdout since the last newline (with sink != None), used as the
    # default prompt label when a script calls input() right after a stdout
    # write.  Reset whenever the sink changes.
    _last_output_tail = ''

    def set_active_sink(self, sink):
        """Direct subsequent subprocess output to ``sink``.

        ``sink`` is an EditorWindow (with .write_output/.clear_output) for a
        script Run, or None to send output to this Console window.
        """
        self.active_sink = sink
        self._last_output_tail = ''

    @staticmethod
    def _tags_indicate_error(tags):
        if not tags:
            return False
        if isinstance(tags, str):
            return 'stderr' in tags.lower() or 'error' in tags.lower()
        return any('stderr' in str(t).lower() or 'error' in str(t).lower()
                   for t in tags)

    def set_warning_stream(self, stream):
        global warning_stream
        warning_stream = stream

    def get_warning_stream(self):
        return warning_stream

    def beginexecuting(self):
        "Helper for ModifiedInterpreter"
        self.resetoutput()
        self.executing = True

    def endexecuting(self):
        "Helper for ModifiedInterpreter"
        perflog.mark("PyShell.endexecuting: begin")
        # Flush any pending buffered output so it's visible before the prompt.
        if getattr(self, '_write_flush_id', None) is not None:
            try:
                self.text.after_cancel(self._write_flush_id)
            except Exception:
                pass
            self._flush_writes()
        self.executing = False
        self.canceled = False
        self.showprompt()
        # try:
        #     self.flist.set_run_indicator(False)
        # except Exception:
        #     pass
        perflog.mark("PyShell.endexecuting: done")

    def show(self):
        "Make the console window visible and active."
        try:
            if getattr(self, 'menubar', None) is not None:
                self.top.config(menu=self.menubar)
            self._desired_visible = True
            self.top.deiconify()
            # Flush pending widget draws so the text content is submitted to
            # the macOS compositor before the window is presented.  Without
            # this the window can appear momentarily blank.
            self.top.update_idletasks()
        except TclError:
            pass

    def close(self):
        "Override EditorWindow.close(): a direct close of the Console hides it."
        # The Console is permanently open while PEM runs; closing its window by
        # any means only hides it (see PyShellFileList.hide_shell).  It is shut
        # down for real -- subprocess killed, window destroyed -- only when PEM
        # exits, via PyShellFileList.close_all_callback() calling self._close().
        self.flist.hide_shell()
        return "break"

    def _close(self):
        "Extend EditorWindow._close(), shut down execution server"
        # Break out of any pending readline (input()) loop and flag shutdown so
        # the execution subprocess and begin()/show() failsafes behave.
        self.stop_readline()
        self.canceled = True
        self.closing = True
        if use_subprocess and self.interp and self.interp.rpcsubproc:
            self.interp.kill_subprocess()
        # Restore std streams
        sys.stdout = self.save_stdout
        sys.stderr = self.save_stderr
        sys.stdin = self.save_stdin
        # Break cycles
        self.interp = None
        self.console = None
        self.flist.pyshell = None
        self.history = None
        EditorWindow._close(self)

    def ispythonsource(self, filename):
        "Override EditorWindow method: never remove the colorizer"
        return True

    def short_title(self):
        return self.shell_title

    def begin(self):
        perflog.mark("PyShell.begin: start (will boot execution subprocess)")
        # --- SHUTDOWN FAILSAFE ---
        # Abort if the widget is already gone or the app is closing.
        if getattr(self, 'text', None) is None or getattr(self, 'closing', False):
            return False

        try:
            self.text.mark_set("iomark", "insert")
            self.resetoutput()
        except (AttributeError, TclError):
            return False

        if use_subprocess:
            client = self.interp.start_subprocess()
            if not client:
                self.close()
                return False
        else:
            sys.displayhook = rpc.displayhook

        try:
            from PythonMusic import __version__ as cp_version
            self.write("PythonMusic %s\n" % cp_version)
        except Exception:
            pass
            
        self.write("Python %s on %s\n\n" %
                   (sys.version, sys.platform))
        
        # --- FIX: Ensure the widget still exists before focusing ---
        if self.text is not None and not getattr(self, 'closing', False):
            try:
                # Do not force keyboard focus to an invisible window!
                if hasattr(self, 'top') and self.top.state() == 'normal':
                    self.text.focus_force()
            except (TclError, AttributeError):
                pass
            
        self.showprompt()

        self.top.wm_title(self.shell_title)

        # Closing the Console hides it rather than destroying it, no matter how
        # the close is triggered: the window's close button, Cmd/Ctrl+W, or the
        # Close menu item (which all fire <<close-window>>).
        def _hide_console(event=None):
            self.flist.hide_shell()
            return "break"
        self.top.protocol("WM_DELETE_WINDOW", _hide_console)
        self.text.bind("<<close-window>>", _hide_console)
        self.top.bind("<<close-window>>", _hide_console)

        # User code should use separate default Tk root window
        import tkinter
        tkinter._support_default_root = True
        tkinter._default_root = None
        perflog.mark("PyShell.begin: done")
        return True


    def stop_readline(self):
        if not self.reading:  # no nested mainloop to exit.
            return
        self._stop_readline_flag = True
        self.top.quit()

    def readline(self):
        # RPC entry point for subprocess input() / sys.stdin.readline().
        # Dispatch by self.active_sink (set by the run dispatcher):
        #   sink is an EditorWindow -> pop a modal dialog (the output pane is
        #     display-only); the typed answer is echoed into the pane so the
        #     transcript is complete.
        #   sink is None            -> nested mainloop, user types into this
        #     Console (the IDLE-derived behavior).
        # Flush any pending buffered output so the prompt context is on-screen
        # before we block for user input.
        if getattr(self, '_write_flush_id', None) is not None:
            try:
                self.text.after_cancel(self._write_flush_id)
            except Exception:
                pass
            self._flush_writes()
        sink = self.active_sink
        if (sink is not None
                and hasattr(sink, 'write_output')
                and getattr(sink, 'top', None) is not None):
            try:
                widget_ok = bool(sink.top.winfo_exists())
            except Exception:
                widget_ok = False
            if widget_ok:
                prompt = (self._last_output_tail or '').rstrip()
                try:
                    answer = simpledialog.askstring(
                        "Input", prompt, parent=sink.text) or ""
                except Exception:
                    answer = ""
                try:
                    sink.write_output(answer + "\n", is_error=False)
                except Exception:
                    pass
                self._last_output_tail = ''
                return answer + "\n"

        # Default: read a line typed into this Console window.
        save = self.reading
        try:
            self.reading = True
            self.top.mainloop()  # nested mainloop()
        finally:
            self.reading = save
        if self._stop_readline_flag:
            self._stop_readline_flag = False
            return ""

        # --- SHUTDOWN FAILSAFE: Check if text still exists ---
        if self.text is None:
            return ""

        line = self.text.get("iomark", "end-1c")
        if len(line) == 0:  # may be EOF if we quit our mainloop with Ctrl-C
            line = "\n"
        self.resetoutput()
        if self.canceled:
            self.canceled = False
            if not use_subprocess:
                raise KeyboardInterrupt
        if self.endoffile:
            self.endoffile = False
            line = ""
        return line

    def isatty(self):
        return True

    def cancel_callback(self, event=None):
        try:
            if self.text.compare("sel.first", "!=", "sel.last"):
                return # Active selection -- always use default binding
        except:
            pass
        if not (self.executing or self.reading):
            self.resetoutput()
            self.interp.write("KeyboardInterrupt\n")
            self.showprompt()
            return "break"
        self.endoffile = False
        self.canceled = True
        if (self.executing and self.interp.rpcclt):
            self.interp.interrupt_subprocess()
        if self.reading:
            self.top.quit()  # exit the nested mainloop() in readline()
        return "break"

    def eof_callback(self, event):
        if self.executing and not self.reading:
            return # Let the default binding (delete next char) take over
        if not (self.text.compare("iomark", "==", "insert") and
                self.text.compare("insert", "==", "end-1c")):
            return # Let the default binding (delete next char) take over
        if not self.executing:
            self.resetoutput()
            self.close()
        else:
            self.canceled = False
            self.endoffile = True
            self.top.quit()
        return "break"

    def linefeed_callback(self, event):
        # Insert a linefeed without entering anything (still autoindented)
        if self.reading:
            self.text.insert("insert", "\n")
            self.text.see("insert")
        else:
            self.newline_and_indent_event(event)
        return "break"

    def enter_callback(self, event):
        if self.executing and not self.reading:
            return # Let the default binding (insert '\n') take over
        # If some text is selected, recall the selection
        # (but only if this before the I/O mark)
        try:
            sel = self.text.get("sel.first", "sel.last")
            if sel:
                if self.text.compare("sel.last", "<=", "iomark"):
                    self.recall(sel, event)
                    return "break"
        except:
            pass
        # If we're strictly before the line containing iomark, recall
        # the current line, less a leading prompt, less leading or
        # trailing whitespace
        if self.text.compare("insert", "<", "iomark linestart"):
            # Check if there's a relevant stdin range -- if so, use it.
            # Note: "stdin" blocks may include several successive statements,
            # so look for "console" tags on the newline before each statement
            # (and possibly on prompts).
            prev = self.text.tag_prevrange("stdin", "insert")
            if (
                    prev and
                    self.text.compare("insert", "<", prev[1]) and
                    # The following is needed to handle empty statements.
                    "console" not in self.text.tag_names("insert")
            ):
                prev_cons = self.text.tag_prevrange("console", "insert")
                if prev_cons and self.text.compare(prev_cons[1], ">=", prev[0]):
                    prev = (prev_cons[1], prev[1])
                next_cons = self.text.tag_nextrange("console", "insert")
                if next_cons and self.text.compare(next_cons[0], "<", prev[1]):
                    prev = (prev[0], self.text.index(next_cons[0] + "+1c"))
                self.recall(self.text.get(prev[0], prev[1]), event)
                return "break"
            next = self.text.tag_nextrange("stdin", "insert")
            if next and self.text.compare("insert lineend", ">=", next[0]):
                next_cons = self.text.tag_nextrange("console", "insert lineend")
                if next_cons and self.text.compare(next_cons[0], "<", next[1]):
                    next = (next[0], self.text.index(next_cons[0] + "+1c"))
                self.recall(self.text.get(next[0], next[1]), event)
                return "break"
            # No stdin mark -- just get the current line, less any prompt
            indices = self.text.tag_nextrange("console", "insert linestart")
            if indices and \
               self.text.compare(indices[0], "<=", "insert linestart"):
                self.recall(self.text.get(indices[1], "insert lineend"), event)
            else:
                self.recall(self.text.get("insert linestart", "insert lineend"), event)
            return "break"
        # If we're between the beginning of the line and the iomark, i.e.
        # in the prompt area, move to the end of the prompt
        if self.text.compare("insert", "<", "iomark"):
            self.text.mark_set("insert", "iomark")
        # If we're in the current input and there's only whitespace
        # beyond the cursor, erase that whitespace first
        s = self.text.get("insert", "end-1c")
        if s and not s.strip():
            self.text.delete("insert", "end-1c")
        # If we're in the current input before its last line,
        # insert a newline right at the insert point
        if self.text.compare("insert", "<", "end-1c linestart"):
            self.newline_and_indent_event(event)
            return "break"
        # We're in the last line; append a newline and submit it
        self.text.mark_set("insert", "end-1c")
        if self.reading:
            self.text.insert("insert", "\n")
            self.text.see("insert")
        else:
            self.newline_and_indent_event(event)
        self.text.update_idletasks()
        if self.reading:
            self.top.quit() # Break out of recursive mainloop()
        else:
            self.runit()
        return "break"

    def recall(self, s, event):
        # remove leading and trailing empty or whitespace lines
        s = re.sub(r'^\s*\n', '', s)
        s = re.sub(r'\n\s*$', '', s)
        lines = s.split('\n')
        self.text.undo_block_start()
        try:
            self.text.tag_remove("sel", "1.0", "end")
            self.text.mark_set("insert", "end-1c")
            prefix = self.text.get("insert linestart", "insert")
            if prefix.rstrip().endswith(':'):
                self.newline_and_indent_event(event)
                prefix = self.text.get("insert linestart", "insert")
            self.text.insert("insert", lines[0].strip(),
                             self.user_input_insert_tags)
            if len(lines) > 1:
                orig_base_indent = re.search(r'^([ \t]*)', lines[0]).group(0)
                new_base_indent  = re.search(r'^([ \t]*)', prefix).group(0)
                for line in lines[1:]:
                    if line.startswith(orig_base_indent):
                        # replace orig base indentation with new indentation
                        line = new_base_indent + line[len(orig_base_indent):]
                    self.text.insert('insert', '\n' + line.rstrip(),
                                     self.user_input_insert_tags)
        finally:
            self.text.see("insert")
            self.text.undo_block_stop()


    _last_newline_re = re.compile(r"[ \t]*(\n[ \t]*)?\Z")
    
    def runit(self):
        # --- SHUTDOWN FAILSAFE ---
        if self.text is None:
            return

        # Console-entered code's output belongs in this Console window, not in
        # a previously-targeted editor tab's output pane.
        self.set_active_sink(None)

        line = self.text.get("iomark", "end-1c")
        #print(f"[runit] line={line!r}")                                  # debug

        # Strip off last newline and surrounding whitespace.
        # (To allow you to hit return twice to end a statement.)
        clean_line = self._last_newline_re.sub("", line)
        #print(f"[runit] clean_line={clean_line!r}")                      # debug

        input_is_complete = self.interp.runsource(clean_line)
        #print(f"[runit] runsource returned {input_is_complete!r} "       # debug
        #      f"(True=incomplete, False=complete-or-syntax-error)")

        if not input_is_complete:
            trailing_match = re.search(r'(?:\n[ \t]*){2,}\Z', line)
            # ---------------------------------------------------------
            # SUBSYSTEM: MULTILINE PROMPT CLEANUP
            # When the input is recognized as complete, the buffer often
            # has more trailing newlines than the displayed transcript
            # should keep — typically a "blank" continuation line the user
            # pressed Return on to terminate the statement. Delete those
            # surplus newlines from the buffer so the executed block reads
            # cleanly and only one (...) continuation line remains before
            # the next ">>>" prompt.
            # ---------------------------------------------------------
            if trailing_match:
                delete_length = len(trailing_match.group(0)) - 1
                delete_start = f"end-1c - {delete_length} chars"
                # runsource() above moved iomark to end-1c via beginexecuting()
                # → resetoutput(). The ModifiedUndoDelegator rings the bell on
                # any delete behind iomark. Briefly move iomark out of the way
                # for this internal cleanup, then restore it.
                self.text.mark_set("iomark", "1.0")
                self.text.delete(delete_start, "end-1c")
                self.text.mark_set("iomark", "end-1c")

            self.shell_sidebar.update_sidebar()

    def view_restart_mark(self, event=None):
        self.text.see("iomark")
        self.text.see("restart")

    def new_callback(self, event):
        """Create new editor window, inheriting interpreter's working directory."""
        dirname = self.flist.interp_cwd
        if dirname is None:
            dirname, _ = self.io.defaultfilename()
        self.flist.new(dirname)
        return "break"

    def restart_shell(self, event=None):
        "Restart the execution subprocess (Restart Console menu item / Stop button / Ctrl-F6)."
        self.interp.restart_subprocess(with_cwd=True)

    def _stop_subprocess(self):
        """Shared subprocess restart logic used by both Stop and Reset."""
        try:
            if self.interp and self.interp.rpcclt:
                self.restart_shell()
        except Exception:
            pass

    def toolbar_stop(self):
        """Stop the running script; keep the Console window open and its history intact."""
        self._stop_subprocess()

    def toolbar_reset(self):
        """Reset: stop the subprocess and restore the console to its initial startup state."""
        self._stop_subprocess()
        try:
            self.per.bottom.delete('1.0', 'end')
            self.text.mark_set('iomark', 'end-1c')
        except Exception:
            pass
        try:
            from PythonMusic import __version__ as cp_version
            self.write("PythonMusic %s\n" % cp_version)
        except Exception:
            pass
        try:
            self.write("Python %s on %s\n" % (sys.version, sys.platform))
            self.write_to_console("\n======= Reset =======\n", "stdout")
            self.showprompt()
        except Exception:
            pass

    def showprompt(self):
        # --- SHUTDOWN FAILSAFE: Intercept Phantom Restarts ---
        if getattr(self, 'text', None) is None or getattr(self, 'closing', False):
            return

        self.resetoutput()

        prompt = self.prompt
        if self.sys_ps1 and prompt.endswith(self.sys_ps1):
            prompt = prompt[:-len(self.sys_ps1)]
        
        try:
            self.text.tag_add("console", "iomark-1c")
            self.console.write(prompt)
            if hasattr(self, 'shell_sidebar') and self.shell_sidebar:
                self.shell_sidebar.update_sidebar()
            self.text.mark_set("insert", "end-1c")
            self.set_line_and_column()
            self.io.reset_undo()
        except (AttributeError, TclError):
            pass

    def show_warning(self, msg):
        width = self.interp.tkconsole.width
        wrapper = TextWrapper(width=width, tabsize=8, expand_tabs=True)
        wrapped_msg = '\n'.join(wrapper.wrap(msg))
        if not wrapped_msg.endswith('\n'):
            wrapped_msg += '\n'
        self.per.bottom.insert("iomark linestart", wrapped_msg, "stderr")

    def resetoutput(self):
        # --- SHUTDOWN FAILSAFE: Abort if widget is gone ---
        if self.text is None:
            return

        source = self.text.get("iomark", "end-1c")
        if self.history:
            self.history.store(source)
        if self.text.get("end-2c") != "\n":
            self.text.insert("end-1c", "\n")
        self.text.mark_set("iomark", "end-1c")
        self.set_line_and_column()
        self.io.reset_undo()

    def write_to_console(self, s, tags=()):
        """Write straight into this Console window's text widget, ignoring
        active_sink -- for RESTART banners and other Console-only annotations.

        Deliberately does NOT call self.text.update() (unlike OutputWindow.write),
        because this is called from restart_subprocess() while self.restarting is
        True: a re-entrant Tk event pump there could process a queued Run/Stop
        click and wedge the restart flag.
        """
        if getattr(self, 'closing', False) or self.text is None:
            return 0
        try:
            self.text.mark_gravity("iomark", "right")   # text lands before the input mark
            # Treat embedded \r terminal-style so tqdm progress bars collapse
            # to one updating line instead of thousands of stacked ones.
            # Bypass the iomark-protection wrapper for the overwrite delete:
            # self.text refuses modifications before iomark (bell + no-op), but
            # the raw Text widget at self.per.bottom allows it.
            s_norm = s.replace('\r\n', '\n')
            parts = s_norm.split('\r')
            self.text.insert("iomark", parts[0], tags)
            for part in parts[1:]:
                self.per.bottom.delete("iomark linestart", "iomark")
                self.text.insert("iomark", part, tags)
            if self.text:
                self.text.mark_gravity("iomark", "left")
                self.text.see("iomark")
            return len(s)
        except (AttributeError, TclError):
            return 0

    def write(self, s, tags=()):
        # RPC entry point for subprocess output (stdout / stderr / script
        # print()).  Routes by self.active_sink:
        #   sink is an EditorWindow  -> write to that tab's output pane
        #   sink is None             -> write to this Console's text widget
        # Immediate-render path -- used by internal GUI code that emits
        # banners, prompts, syntax errors, etc., and needs the text on screen
        # synchronously so subsequent writes / mark moves don't reorder
        # against it.  Subprocess output goes through write_subprocess()
        # instead, which buffers for throughput.
        if getattr(self, 'closing', False) or self.text is None:
            return 0

        sink = self.active_sink
        if (sink is not None
                and hasattr(sink, 'write_output')
                and getattr(sink, 'top', None) is not None):
            try:
                if not sink.top.winfo_exists():
                    sink = None
            except Exception:
                sink = None
        else:
            sink = None

        if sink is not None:
            is_error = self._tags_indicate_error(tags)
            try:
                sink.write_output(s, is_error=is_error)
            except Exception:
                return 0
            if not is_error:
                combined = self._last_output_tail + s
                nl = combined.rfind('\n')
                self._last_output_tail = combined[nl + 1:] if nl >= 0 else combined
            self.write_to_console(s, tags)
            return len(s)

        if not getattr(self, '_perf_first_write_logged', False):
            self._perf_first_write_logged = True
            perflog.mark("PyShell.write: first output written to Console window")
        count = self.write_to_console(s, tags)
        if getattr(self, 'canceled', False):
            self.canceled = False
            if not getattr(self, 'closing', False):
                raise KeyboardInterrupt
        return count

    def write_subprocess(self, s, tags=()):
        """Buffered write path: the subprocess RPC target (see
        ``execution.run.StdOutputFile.write``).  Each subprocess write enqueues
        a chunk and returns immediately so the RPC ACK is fast; a periodic
        flush coalesces a burst (tqdm progress bars, print loops) into one
        batched render.  Without this, the subprocess's effective write rate
        is gated by per-chunk Tk work -- a tqdm-instrumented download can slow
        from MB/s to KB/s waiting for each RPC to round-trip."""
        if getattr(self, 'closing', False) or self.text is None:
            return 0

        is_error = self._tags_indicate_error(tags)
        # Update the input() prompt-label tail synchronously: a quick input()
        # after a print() needs to see the up-to-date tail, even if the
        # rendering of the print() is still buffered.
        if not is_error:
            combined = self._last_output_tail + s
            nl = combined.rfind('\n')
            self._last_output_tail = combined[nl + 1:] if nl >= 0 else combined

        if not hasattr(self, '_write_buffer'):
            self._write_buffer = []
            self._write_flush_id = None
        self._write_buffer.append((s, tags, is_error))
        if self._write_flush_id is None:
            self._write_flush_id = self.text.after(16, self._flush_writes)

        if getattr(self, 'canceled', False):
            self.canceled = False
            if not getattr(self, 'closing', False):
                raise KeyboardInterrupt
        return len(s)

    def _flush_writes(self):
        """Drain the buffered write chunks: resolve sink once, merge runs of
        same-tag chunks, and dispatch each merged chunk to the sink's output
        pane and this Console's mirror."""
        self._write_flush_id = None
        buf = self._write_buffer
        self._write_buffer = []
        if not buf or getattr(self, 'closing', False) or self.text is None:
            return

        sink = self.active_sink
        if (sink is not None
                and hasattr(sink, 'write_output')
                and getattr(sink, 'top', None) is not None):
            try:
                if not sink.top.winfo_exists():
                    sink = None
            except Exception:
                sink = None
        else:
            sink = None

        # Merge consecutive chunks that share both (tags, is_error) so each
        # downstream renderer call is one big chunk instead of many small ones.
        merged = []
        cur_s, cur_tags, cur_is_error = buf[0]
        for s, tags, is_error in buf[1:]:
            if tags == cur_tags and is_error == cur_is_error:
                cur_s += s
            else:
                merged.append((cur_s, cur_tags, cur_is_error))
                cur_s, cur_tags, cur_is_error = s, tags, is_error
        merged.append((cur_s, cur_tags, cur_is_error))

        if not getattr(self, '_perf_first_write_logged', False):
            self._perf_first_write_logged = True
            perflog.mark("PyShell.write_subprocess: first output flushed")

        for s, tags, is_error in merged:
            if sink is not None:
                try:
                    sink.write_output(s, is_error=is_error)
                except Exception:
                    sink = None  # fall back to console-only for the rest
            self.write_to_console(s, tags)

    def rmenu_check_cut(self):
        try:
            if self.text.compare('sel.first', '<', 'iomark'):
                return 'disabled'
        except TclError: # no selection, so the index 'sel.first' doesn't exist
            return 'disabled'
        return super().rmenu_check_cut()

    def rmenu_check_paste(self):
        if self.text.compare('insert','<','iomark'):
            return 'disabled'
        return super().rmenu_check_paste()

    def up_arrow_callback(self, event=None):
        """Handle up arrow key - navigate history if at prompt, else allow normal navigation"""
        # only use history navigation when cursor is at or after iomark (in input area)
        if self.text.compare("insert", ">=", "iomark"):
            self.history.history_prev(event)
            return "break"
        return None   # allow default behavior for navigating output

    def down_arrow_callback(self, event=None):
        """Handle down arrow key - navigate history if at prompt, else allow normal navigation"""
        # only use history navigation when cursor is at or after iomark (in input area)
        if self.text.compare("insert", ">=", "iomark"):
            self.history.history_next(event)
            return "break"
        return None   # allow default behavior for navigating output

    def squeeze_current_text_event(self, event=None):
        self.squeezer.squeeze_current_text()
        self.shell_sidebar.update_sidebar()

    def on_squeezed_expand(self, index, text, tags):
        self.shell_sidebar.update_sidebar()


def fix_x11_paste(root):
    "Make paste replace selection on x11.  See issue #5124."
    if root._windowingsystem == 'x11':
        for cls in 'Text', 'Entry', 'Spinbox':
            root.bind_class(
                cls,
                '<<Paste>>',
                'catch {%W delete sel.first sel.last}\n' +
                        root.bind_class(cls, '<<Paste>>'))


usage_msg = """\

USAGE: pem  [-eins] [-t title] [file]*
       pem  [-ns] [-t title] (-c cmd | -r file) [arg]*
       pem  [-ns] [-t title] - [arg]*

  -h         print this help message and exit
  -n         run PEM without a subprocess (DEPRECATED,
             see Help/PEM Help for details)

The following options will override the PEM 'settings' configuration:

  -e         open an edit window
  -i         open a shell window

The following options imply -i and will open a shell:

  -c cmd     run the command in a shell, or
  -r file    run script from file

  -s         run $PEMSTARTUP or $PYTHONSTARTUP before anything else
  -t title   set title of shell window

A default edit window will be bypassed when -c, -r, or - are used.

[arg]* are passed to the command (-c) or script (-r) in sys.argv[1:].

Examples:

pem
        Open an edit window or shell depending on PEM's configuration.

pem foo.py foobar.py
        Edit the files, also open a shell if configured to start with shell.

pem -est "Baz" foo.py
        Run $PEMSTARTUP or $PYTHONSTARTUP, edit foo.py, and open a shell
        window with the title "Baz".

pem -c "import sys; print(sys.argv)" "foo"
        Open a shell window and run the command, passing "-c" in sys.argv[0]
        and "foo" in sys.argv[1].

pem -s -r foo.py "Hello World"
        Open a shell window, run a startup script, and
        run foo.py, passing "foo.py" in sys.argv[0] and "Hello World" in
        sys.argv[1].

echo "import sys; print(sys.argv)" | pem - "foobar"
        Open a shell window, run the script piped in, passing '' in sys.argv[0]
        and "foobar" in sys.argv[1].
"""

def _ensure_save_panel_expanded():
    """On macOS, default NSSavePanel to the expanded (full-browser) view for
    first-time users.  The preference is per-bundle-id and persisted in
    ~/Library/Preferences/PEM.plist; we only write it if unset, so the user's
    own later choice to collapse the panel is preserved.
    """
    if sys.platform != 'darwin':
        return
    import subprocess
    bundleId = 'PEM'
    keys = ('NSNavPanelExpandedStateForSaveMode',
            'NSNavPanelExpandedStateForSaveMode2')
    for key in keys:
        try:
            existing = subprocess.run(['defaults', 'read', bundleId, key],
                                      capture_output=True, text=True, timeout=5)
            if existing.returncode == 0:
                continue   # already set; leave the user's preference alone
            subprocess.run(['defaults', 'write', bundleId, key, '-bool', 'YES'],
                           capture_output=True, timeout=5)
        except (OSError, subprocess.SubprocessError):
            return   # non-fatal; just skip on any failure


def main():
    import getopt
    from platform import system
    from pem import testing  # bool value
    from pem import macosx

    global flist, root, use_subprocess

    # Name the app before any Tk()/NSApplication is created, so macOS shows
    # 'PEM' in the menu bar and Dock instead of 'Python' (the executable name).
    macosx.setApplicationName('PEM')

    _ensure_save_panel_expanded()
    capture_warnings(True)
    use_subprocess = True
    enable_shell = False
    enable_edit = False
    cmd = None
    script = None
    startup = False
    try:
        opts, args = getopt.getopt(sys.argv[1:], "c:eihnr:st:")
    except getopt.error as msg:
        print(f"Error: {msg}\n{usage_msg}", file=sys.stderr)
        sys.exit(2)
    for o, a in opts:
        if o == '-c':
            cmd = a
            enable_shell = True
        if o == '-e':
            enable_edit = True
        if o == '-h':
            sys.stdout.write(usage_msg)
            sys.exit()
        if o == '-i':
            enable_shell = True
        if o == '-n':
            # print(" Warning: running PEM without a subprocess is deprecated.",
            #       file=sys.stderr)
            use_subprocess = False
        if o == '-r':
            script = a
            if os.path.isfile(script):
                pass
            else:
                print("No script file: ", script)
                sys.exit()
            enable_shell = True
        if o == '-s':
            startup = True
            enable_shell = True
        if o == '-t':
            PyShell.shell_title = a
            enable_shell = True
    if args and args[0] == '-':
        cmd = sys.stdin.read()
        enable_shell = True
    # process sys.argv and sys.path:
    for i in range(len(sys.path)):
        sys.path[i] = os.path.abspath(sys.path[i])
    if args and args[0] == '-':
        sys.argv = [''] + args[1:]
    elif cmd:
        sys.argv = ['-c'] + args
    elif script:
        sys.argv = [script] + args
    elif args:
        enable_edit = True
        pathx = []
        for filename in args:
            pathx.append(os.path.dirname(filename))
        for dir in pathx:
            dir = os.path.abspath(dir)
            if not dir in sys.path:
                sys.path.insert(0, dir)
    else:
        dir = os.getcwd()
        if dir not in sys.path:
            sys.path.insert(0, dir)
    # check the PEM settings configuration (but command line overrides)
    edit_start = pemConf.GetOption('main', 'General',
                                    'editor-on-startup', type='bool')
    enable_edit = enable_edit or edit_start
    enable_shell = enable_shell or not enable_edit

    # Setup root.  Don't break user code run in PEM process.
    # Don't change environment when testing.
    if use_subprocess and not testing:
        NoDefaultRoot()
    root = Tk(className="Pem")
    root.withdraw()
    from pem.util import fix_scaling
    fix_scaling(root)

    # set application icon
    icondir = os.path.join(os.path.dirname(__file__), 'icons')
    if system() == 'Windows':
        iconfile = os.path.join(icondir, 'icon.ico')
        root.wm_iconbitmap(default=iconfile)
    elif not macosx.isAquaTk():
        iconfile = os.path.join(icondir, 'icon_rounded.png')
        if os.path.exists(iconfile):
            icon = PhotoImage(master=root, file=iconfile)
            root.wm_iconphoto(True, icon)

    # start editor and/or shell windows:
    fixwordbreaks(root)
    fix_x11_paste(root)
    flist = PyShellFileList(root)
    macosx.setupApp(root, flist)

    # Determine initial working directory for blank editor windows.
    # For a frozen app: use the directory containing the app/executable.
    # On macOS the executable lives inside PEM.app/Contents/MacOS/, so
    # walk up to find the .app bundle and return its parent directory.
    # For development (running PEM.py): use the launch cwd.
    if getattr(sys, 'frozen', False):
        _exe = os.path.abspath(sys.executable)
        _launch_dir = os.path.dirname(_exe)
        _p = _exe
        for _ in range(8):
            _p = os.path.dirname(_p)
            if _p == os.path.dirname(_p):  # filesystem root, give up
                break
            if os.path.basename(_p).endswith('.app'):
                _launch_dir = os.path.dirname(_p)
                break
    else:
        _launch_dir = os.getcwd()
    flist.interp_cwd = _launch_dir

    if enable_edit:
        if not (cmd or script):
            for filename in args[:]:
                if flist.open(filename) is None:
                    # filename is a directory actually, disconsider it
                    args.remove(filename)
            if not args:
                flist.new(_launch_dir)

    if enable_shell:
        shell = flist.open_shell()
        if not shell:
            return # couldn't open shell
        if macosx.isAquaTk() and flist.dict:
            # On OSX: when the user has double-clicked on a file that causes
            # PEM to be launched the shell window will open just in front of
            # the file she wants to see. Lower the interpreter window when
            # there are open files.
            shell.top.lower()
    else:
        shell = flist.pyshell

    # Handle remaining options. If any of these are set, enable_shell
    # was set also, so shell must be true to reach here.
    if startup:
        filename = os.environ.get("PEMSTARTUP") or \
                   os.environ.get("PYTHONSTARTUP")
        if filename and os.path.isfile(filename):
            shell.interp.execfile(filename)
    if cmd or script:
        shell.interp.runcommand("""if 1:
            import sys as _sys
            _sys.argv = {!r}
            del _sys
            \n""".format(sys.argv))
        if cmd:
            shell.interp.execsource(cmd)
        elif script:
            shell.interp.prepend_syspath(script)
            shell.interp.execfile(script)
    elif shell:
        # If there is a shell window and no cmd or script in progress,
        # check for problematic issues and print warning message(s) in
        # the PEM shell window; this is less intrusive than always
        # opening a separate window.

        # Warn if the "Prefer tabs when opening documents" system
        # preference is set to "Always".
        prefer_tabs_preference_warning = macosx.preferTabsPreferenceWarning()
        if prefer_tabs_preference_warning:
            shell.show_warning(prefer_tabs_preference_warning)

    while flist.inversedict:  # keep PEM running while files are open.
        root.mainloop()

    # *** (should we do it here, or when the main editor window closes?)
    # save sash and other window geometry permanently to file on shutdown
    # try:
    #     from pem.config import pemConf
    #     pemConf.userCfg['main'].Save()
    # except Exception:
    #     pass

    root.destroy()
    capture_warnings(False)


if __name__ == "__main__":
    main()

capture_warnings(False)  # Make sure turned off; see issue 18081
