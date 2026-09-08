"""Manage the Python subprocesses that run the user's code.

``Interpreter`` owns the pair of subprocesses PEM keeps: the active one
that user code runs in, and a pre-warmed spare waiting in the wings.  Run and
Stop both perform the same handoff -- promote the spare, tear down the old
process off the Tk thread, and start building the next spare -- so a Run never
waits for a process to start.  The manager also holds the RPC connection to
the active subprocess and runs the poll loop that pumps its responses, and its
stdout/stderr callbacks, back into the GUI.

The subprocess at the other end of that connection is a separate, near-bare
Python process; see ``pem.interpreter.run``.

The manager renders through a console window, passed in as ``console``, and
reads what to run from the windows that ask it to run something.
"""
import linecache
import os
import os.path
import re
import signal
import socket
import subprocess
import sys
import threading
import time
import tokenize
from code import InteractiveInterpreter

from tkinter import messagebox

from pem import perflog
from pem.interpreter import rpc

HOST = '127.0.0.1' # python execution server on localhost loopback
PORT = 0  # someday pass in host, port for remote debug capability

# Marker passed to a frozen build's own executable when it is re-launched as
# the execution subprocess.  Must match PEM.py's SUBPROCESS_FLAG.
SUBPROCESS_FLAG = '--pem-subprocess'


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


class Interpreter(InteractiveInterpreter):
    """Runs the user's code, in subprocesses it manages itself.

    Compiles what the windows hand it (via ``code.InteractiveInterpreter``) but
    runs it in a separate process, reached over the RPC socket in
    ``pem.interpreter.rpc``.  It spawns and connects to that process
    (``start_subprocess``), keeps a pre-warmed ``_spare`` ready and promotes it
    on ``stop``/``restart_subprocess``, tears the old process down away from the
    Tk thread, and pumps RPC responses -- and the subprocess's output callbacks
    -- back into the GUI on a timer (``poll_subprocess``).
    """

    def __init__(self, console):
        self.console = console
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
        and runs pem.interpreter.run.main().
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
                     f"from pem.interpreter.run import main; main()")
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
        self.rpcclt.register("console", self.console)
        self.rpcclt.register("stdin", self.console.stdin)
        self.rpcclt.register("stdout", self.console.stdout)
        self.rpcclt.register("stderr", self.console.stderr)
        self.rpcclt.register("flist", self.console.flist)
        self.rpcclt.register("linecache", linecache)
        self.rpcclt.register("interp", self)
        self.transfer_path(with_cwd=True)
        # Apply the desired initial working directory in the subprocess
        target_cwd = self.console.flist.interp_cwd
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
            clt.register("console", self.console)
            clt.register("stdin", self.console.stdin)
            clt.register("stdout", self.console.stdout)
            clt.register("stderr", self.console.stderr)
            clt.register("flist", self.console.flist)
            clt.register("linecache", linecache)
            clt.register("interp", self)
            # Pre-transfer sys.path (with cwd, like start_subprocess) and the
            # current interpreter cwd, fire-and-forget: RPC requests are handled
            # in order, so this lands before any later runcode on this connection.
            path = [''] + list(sys.path)
            clt.asyncqueue("exec", "runcode",
                ("if 1:\n    import sys as _sys\n    _sys.path = %r\n    del _sys\n" % (path,),), {})
            target_cwd = getattr(self.console.flist, 'interp_cwd', None)
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
        console = self.console
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
                self.console.flist.interp_cwd = cwd
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
                self.console.flist.interp_cwd = os.getcwd()

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
            self.console.text.after_cancel(self._afterid)
        try:
            self.rpcclt.listening_sock.close()
        except AttributeError:  # no socket
            pass
        try:
            self.rpcclt.close()
        except AttributeError:  # no socket
            pass
        self.terminate_subprocess()
        self.console.executing = False
        self.rpcclt = None

    def terminate_subprocess(self):
        "Force-terminate the active subprocess and any pre-built spare."
        _terminate_proc(self.rpcsubproc)
        spare = self._spare
        if spare is not None:
            self._spare = None
            _terminate_conn(spare.clt, spare.proc)

    # --- What the windows ask for -------------------------------------------
    # A window says what it wants done and leaves the subprocess handling here.

    def is_connected(self):
        "True while a subprocess is attached and able to run code."
        return self.rpcclt is not None

    def stop(self):
        """Stop whatever is running, on a fresh subprocess.

        The pre-warmed spare becomes the active subprocess, the old one is torn
        down away from the Tk thread, and the next spare starts building.  Does
        nothing if no subprocess is attached.
        """
        if not self.is_connected():
            return
        try:
            self.restart_subprocess(with_cwd=True)
        except Exception:
            pass

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
            if self.console.closing:
                return
            perflog.mark(f"poll_subprocess: lost connection to subprocess ({type(why).__name__}) -> auto-restarting")
            response = None
            self.active_seq = None
            if self.console.executing:
                self.console.executing = False
            self.restart_subprocess()
        if response:
            perflog.mark(f"poll_subprocess: got response from subprocess ({response[0]!r})")
            self.console.resetoutput()
            self.active_seq = None
            how, what = response
            console = self.console.console
            if how == "OK":
                if what is not None:
                    print(repr(what), file=console)
            elif how == "EXCEPTION":
                pass
            elif how == "ERROR":
                errmsg = "pyshell.Interpreter: Subprocess ERROR:\n"
                print(errmsg, what, file=sys.__stderr__)
                print(errmsg, what, file=console)
            # we received a response to the currently active seq number:
            try:
                self.console.endexecuting()
            except AttributeError:  # shell may have closed
                pass
            perflog.mark("poll_subprocess: endexecuting() returned; rescheduling poll")
        # Reschedule myself
        if not self.console.closing:
            self._afterid = self.console.text.after(
                self.console.pollinterval, self.poll_subprocess)

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
                source = (f"__file__ = r'''{os.path.abspath(filename)}'''\n"
                          + source + "\ndel __file__")
        try:
            code = compile(source, filename, "exec")
        except (OverflowError, SyntaxError):
            self.console.resetoutput()
            print('*** Error in script or command!\n'
                 'Traceback (most recent call last):',
                  file=self.console.stderr)
            InteractiveInterpreter.showsyntaxerror(self, filename)
            self.console.showprompt()
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
        console = self.console
        text = console.text
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
        console.colorize_syntax_error(text, pos)
        console.resetoutput()
        self.write("SyntaxError: %s\n" % msg)
        console.showprompt()

    def showtraceback(self):
        "Extend base class method to reset output properly"
        self.console.resetoutput()
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
        if self.console.executing:
            self.display_executing_dialog()
            return 0
        if self.rpcclt:
            self.rpcclt.remotequeue("exec", "runcode", (code,), {})
        else:
            exec(code, self.locals)
        return 1

    def runcode(self, code):
        "Override base class method"
        if self.console.executing:
            perflog.mark("Interpreter.runcode: called while still executing")
            # If executing is True but we're trying to run new code, check if
            # the subprocess is actually responding. If not, reset state.
            if self.rpcclt is not None and self.active_seq is not None:
               # Check if subprocess is still responding
               try:
                  # Try to poll for response with short timeout
                  response = self.rpcclt.pollresponse(self.active_seq, wait=0.01, maxrequests=4)
                  if response is None:
                     # No response yet, subprocess might be stuck - restart it
                     perflog.mark("Interpreter.runcode: prior run unresponsive -> restarting subprocess")
                     self.restart_subprocess()
               except (EOFError, OSError):
                  # Connection broken, restart subprocess
                  perflog.mark("Interpreter.runcode: prior run's connection broken -> restarting subprocess")
                  self.restart_subprocess()
            else:
               # No active sequence but executing is True - reset state
               self.console.executing = False
               self.active_seq = None
        self.checklinecache()
        try:
            self.console.beginexecuting()
            if self.rpcclt is not None:
                self.active_seq = self.rpcclt.asyncqueue("exec", "runcode",
                                                        (code,), {})
                perflog.mark(f"Interpreter.runcode: queued runcode RPC (seq={self.active_seq})")
            else:
                exec(code, self.locals)
        except SystemExit:
            if not self.console.closing:
                if messagebox.askyesno(
                    "Exit?",
                    "Do you want to exit altogether?",
                    default="yes",
                    parent=self.console.text):
                    raise
                else:
                    self.showtraceback()
            else:
                raise
        except:
            print("PEM internal error in runcode()",
                  file=self.console.stderr)
            self.showtraceback()
            self.console.endexecuting()

    def write(self, s):
        "Override base class method"
        return self.console.stderr.write(s)

    def display_port_binding_error(self):
        messagebox.showerror(
            "Port Binding Error",
            "PEM can't bind to a TCP/IP port, which is necessary to "
            "communicate with its Python execution server.  This might be "
            "because no networking is installed on this computer.  "
            "Run PEM with the -n command line switch to start without a "
            "subprocess and refer to Help/PEM Help 'Running without a "
            "subprocess' for further details.",
            parent=self.console.text)

    def display_no_subprocess_error(self):
        messagebox.showerror(
            "Subprocess Connection Error",
            "PEM's subprocess didn't make connection.\n"
            "See the 'Startup failure' section of the PEM doc, online at\n"
            "https://docs.python.org/3/library/pem.html#startup-failure",
            parent=self.console.text)

    def display_executing_dialog(self):
        messagebox.showerror(
            "Already executing",
            "The Python Console window is already executing a command; "
            "please wait until it is finished.",
            parent=self.console.text)
