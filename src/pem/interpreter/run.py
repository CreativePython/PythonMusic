""" pem.interpreter.run -- the PEM execution subprocess (RPC server).

Spawned by Interpreter.build_subprocess_arglist():
  * from source / an installed pem:
        {sys.executable} -c "...; from pem.interpreter.run import main; main()" <port>
  * from a frozen build: the bundled executable is re-launched with the
        --pem-subprocess flag, which routes into PEM.py -> run.main().
This module deliberately imports nothing from PEM except the RPC layer, so
the subprocess starts as essentially bare Python -- user code imports tkinter
(or anything else) on its own.
"""
import contextlib
import functools
import io
import linecache
import queue
import sys
import textwrap
import time
import traceback
import _thread as thread
import threading
import warnings

from pem import perflog
perflog.mark("run.py: stdlib imports done; importing pem RPC server")

import pem  # for pem.testing
from pem.interpreter import rpc, startup
from pem._encoding import encoding, errors
import __main__
perflog.mark("run.py: module-level imports done")

LOCALHOST = '127.0.0.1'

# Make `exit`/`quit` say "Use exit() or Ctrl-D (end-of-file) to exit"; absent
# if the subprocess is ever started with -S (no site builtins).
try:
    eof = 'Ctrl-D (end-of-file)'
    exit.eof = eof
    quit.eof = eof
except NameError:
    pass


def pem_formatwarning(message, category, filename, lineno, line=None):
    """Format warnings the PEM way."""

    s = "\nWarning (from warnings module):\n"
    s += f'  File \"{filename}\", line {lineno}\n'
    if line is None:
        line = linecache.getline(filename, lineno)
    line = line.strip()
    if line:
        s += "    %s\n" % line
    s += f"{category.__name__}: {message}\n"
    return s

def pem_showwarning_subproc(
        message, category, filename, lineno, file=None, line=None):
    """warnings.showwarning replacement for the subprocess.

    Formats with pem_formatwarning and defaults ``file`` to sys.stderr (which
    is an RPC proxy back to the shell), so user-code warnings appear in PEM.
    """
    if file is None:
        file = sys.stderr
    try:
        file.write(pem_formatwarning(
                message, category, filename, lineno, line))
    except OSError:
        pass # the file (probably stderr) is invalid - this warning gets lost.

_warnings_showwarning = None

def capture_warnings(capture):
    "Replace warning.showwarning with pem_showwarning_subproc, or reverse."

    global _warnings_showwarning
    if capture:
        if _warnings_showwarning is None:
            _warnings_showwarning = warnings.showwarning
            warnings.showwarning = pem_showwarning_subproc
    else:
        if _warnings_showwarning is not None:
            warnings.showwarning = _warnings_showwarning
            _warnings_showwarning = None

capture_warnings(True)

# Thread shared globals
exit_now = False
quitting = False
interruptable = False


# ── GUI event pump for idle ticks ─────────────────────────────────────────────
#
# Why this exists.  A regular Python REPL pumps the GUI event loop "for free":
# CPython's read-line implementation invokes PyOS_InputHook between keystrokes,
# and Qt/Tk bindings register a callback there to keep their windows painting.
# That hook is what makes `plt.show(block=False)` actually display a window
# when you type at a `python -i` prompt.
#
# PEM's execution subprocess doesn't go through readline -- its main loop
# blocks on `rpc.request_queue.get(timeout=0.05)`, so PyOS_InputHook is never
# fired.  Symptom: GUI libraries stall after the user's code returns.
#
# A first attempt at this hook simply invoked PyOS_InputHook from idle ticks.
# That broke PEM: PySide6's hook callback assumes it's running inside CPython's
# `input()` machinery (where stdin is being actively read), and when called
# outside that context it touches state that races against the subprocess's
# own RPC socket writes -- producing interleaved socket bytes, a runcode
# response PEM cannot decode, and a "still executing" / "..." continuation
# symptom.
#
# Instead, drive each toolkit's event queue directly on terms we control.
# Today that means Qt (`QApplication.processEvents()`); tkinter or other
# toolkits would slot in here the same way if a future user needs them.
# Each branch is a no-op when its toolkit hasn't been imported, so users who
# never touch a GUI library pay only the `sys.modules` lookups.

def pump_gui_events():
    """Drive any loaded GUI toolkit's event queue once.

    Called from the RPC main loop's idle ticks.  Per-toolkit branches act
    only when their toolkit is already present in sys.modules and is in a
    state where pumping is meaningful (e.g. a QApplication has been created).
    Errors are swallowed -- a misbehaving toolkit must not bring down user
    code execution.
    """
    # Qt (via PySide6).  Acting only when PySide6.QtWidgets is already in
    # sys.modules means we never import PySide6 ourselves -- user code (or
    # matplotlib's qtagg backend) has to have triggered the import first,
    # which also guarantees a QApplication is ready to receive events.
    qtWidgets = sys.modules.get("PySide6.QtWidgets")
    if qtWidgets is not None:
        try:
            qApp = qtWidgets.QApplication.instance()
            if qApp is not None:
                qApp.processEvents()
        except Exception:
            pass

def main():
    """Run the Python execution server.

    The socket-handling daemon thread (manage_socket -> MyHandler) feeds runcode
    requests from the GUI into rpc.request_queue; this main thread pulls them off
    and executes the user's code, putting results back on rpc.response_queue.
    """
    perflog.mark("run.main(): entered")
    global exit_now
    global quitting

    try:
        assert len(sys.argv) > 1
        port = int(sys.argv[-1])
    except:
        print("PEM Subprocess: no IP port passed in sys.argv.", file=sys.__stderr__)
        return

    # Change the interpreter defaults PEM wants changed for user code
    # this must happen before the socket thread below starts serving the editor's requests.
    startup.apply_startup_settings()

    capture_warnings(True)
    sys.argv[:] = [""]

    threading.Thread(target=manage_socket,
                     name='SockThread',
                     args=((LOCALHOST, port),),
                     daemon=True).start()

    seq = None
    while True:
        try:
            if exit_now:
                try:
                    exit()
                except KeyboardInterrupt:
                    continue

            # Block until the SockThread queues an RPC request, waking
            # periodically so exit_now is re-checked even if no request arrives.
            try:
                seq, (method, args, kwargs) = rpc.request_queue.get(timeout=0.05)
            except queue.Empty:
                # Idle tick -- give any loaded GUI toolkit a chance to paint
                # and process events.  See pump_gui_events above for the
                # rationale (and for why we don't invoke PyOS_InputHook).
                pump_gui_events()
                continue
            ret = method(*args, **kwargs)
            rpc.response_queue.put((seq, ret))

        except KeyboardInterrupt:
            if quitting:
                exit_now = True
            continue
        except SystemExit:
            capture_warnings(False)
            raise
        except:
            type, value, tb = sys.exc_info()
            try:
                print_exception()
                rpc.response_queue.put((seq, None))
            except:
                traceback.print_exception(type, value, tb, file=sys.__stderr__)
                exit()
            else:
                continue

def manage_socket(address):
    global exit_now
    socket_error = None
    # Connect back to the PEM GUI's listening socket.  Normally succeeds on
    # the first try; retry briefly in case the GUI hasn't called accept() yet.
    for attempt in range(8):
        try:
            server = MyRPCServer(address, MyHandler)
            break
        except OSError as err:
            socket_error = err
            time.sleep(0.1)
    else:
        print("PEM Subprocess: Connection to "
              "PEM GUI failed, exiting.", file=sys.__stderr__)
        show_socket_error(socket_error, address)
        exit_now = True
        return
    server.handle_request() # A single request only
    exit_now = True  # socket closed — signal main loop to exit

def show_socket_error(err, address):
    "Report a manage_socket() connection failure."
    # Printed to stderr rather than shown in a tkinter messagebox: the
    # execution subprocess deliberately never imports tkinter.
    print("PEM Subprocess: Connection to "
          f"PEM GUI failed at {address[0]}:{address[1]}.", file=sys.__stderr__)
    print(f"Fatal OSError #{err.errno}: {err.strerror}.", file=sys.__stderr__)


def get_message_lines(typ, exc, tb):
    "Return line composing the exception message."
    if typ in (AttributeError, NameError):
        # 3.10+ hints are not directly accessible from python (#44026).
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            sys.__excepthook__(typ, exc, tb)
        return [err.getvalue().split("\n")[-2] + "\n"]
    else:
        return traceback.format_exception_only(typ, exc)


def print_exception():
    import linecache
    linecache.checkcache()
    flush_stdout()
    efile = sys.stderr
    typ, val, tb = excinfo = sys.exc_info()
    sys.last_type, sys.last_value, sys.last_traceback = excinfo
    sys.last_exc = val
    seen = set()

    def print_exc(typ, exc, tb):
        seen.add(id(exc))
        context = exc.__context__
        cause = exc.__cause__
        if cause is not None and id(cause) not in seen:
            print_exc(type(cause), cause, cause.__traceback__)
            print("\nThe above exception was the direct cause "
                  "of the following exception:\n", file=efile)
        elif (context is not None and
              not exc.__suppress_context__ and
              id(context) not in seen):
            print_exc(type(context), context, context.__traceback__)
            print("\nDuring handling of the above exception, "
                  "another exception occurred:\n", file=efile)
        if tb:
            tbe = traceback.extract_tb(tb)
            print('Traceback (most recent call last):', file=efile)
            exclude = ("run.py", "rpc.py", "threading.py", "queue.py")
            cleanup_traceback(tbe, exclude)
            traceback.print_list(tbe, file=efile)
        lines = get_message_lines(typ, exc, tb)
        for line in lines:
            print(line, end='', file=efile)

    print_exc(typ, val, tb)

def cleanup_traceback(tb, exclude):
    "Remove excluded traces from beginning/end of tb; get cached lines"
    orig_tb = tb[:]
    while tb:
        for rpcfile in exclude:
            if tb[0][0].count(rpcfile):
                break    # found an exclude, break for: and delete tb[0]
        else:
            break        # no excludes, have left RPC code, break while:
        del tb[0]
    while tb:
        for rpcfile in exclude:
            if tb[-1][0].count(rpcfile):
                break
        else:
            break
        del tb[-1]
    if len(tb) == 0:
        # exception was in PEM internals, don't prune!
        tb[:] = orig_tb[:]
        print("** PEM Internal Exception: ", file=sys.stderr)
    rpchandler = rpc.objecttable['exec'].rpchandler
    for i in range(len(tb)):
        fn, ln, nm, line = tb[i]
        if nm == '?':
            nm = "-toplevel-"
        if not line and fn.startswith("<pyshell#"):
            line = rpchandler.remotecall('linecache', 'getline',
                                              (fn, ln), {})
        tb[i] = fn, ln, nm, line

def flush_stdout():
    "No-op: subprocess stdout is unbuffered (each write is its own RPC call)."

def exit():
    "Exit the execution subprocess cleanly."
    capture_warnings(False)
    sys.exit(0)


def fixdoc(fun, text):
    tem = (fun.__doc__ + '\n\n') if fun.__doc__ is not None else ''
    fun.__doc__ = tem + textwrap.fill(textwrap.dedent(text))

RECURSIONLIMIT_DELTA = 30

def install_recursionlimit_wrappers():
    """Install wrappers to always add 30 to the recursion limit."""
    # see: bpo-26806

    @functools.wraps(sys.setrecursionlimit)
    def setrecursionlimit(*args, **kwargs):
        # mimic the original sys.setrecursionlimit()'s input handling
        if kwargs:
            raise TypeError(
                "setrecursionlimit() takes no keyword arguments")
        try:
            limit, = args
        except ValueError:
            raise TypeError(f"setrecursionlimit() takes exactly one "
                            f"argument ({len(args)} given)")
        if not limit > 0:
            raise ValueError(
                "recursion limit must be greater or equal than 1")

        return setrecursionlimit.__wrapped__(limit + RECURSIONLIMIT_DELTA)

    fixdoc(setrecursionlimit, f"""\
            This PEM wrapper adds {RECURSIONLIMIT_DELTA} to prevent possible
            uninterruptible loops.""")

    @functools.wraps(sys.getrecursionlimit)
    def getrecursionlimit():
        return getrecursionlimit.__wrapped__() - RECURSIONLIMIT_DELTA

    fixdoc(getrecursionlimit, f"""\
            This PEM wrapper subtracts {RECURSIONLIMIT_DELTA} to compensate
            for the {RECURSIONLIMIT_DELTA} PEM adds when setting the limit.""")

    # add the delta to the default recursion limit, to compensate
    sys.setrecursionlimit(sys.getrecursionlimit() + RECURSIONLIMIT_DELTA)

    sys.setrecursionlimit = setrecursionlimit
    sys.getrecursionlimit = getrecursionlimit


def uninstall_recursionlimit_wrappers():
    """Uninstall the recursion limit wrappers from the sys module.

    PEM only uses this for tests. Users can import run and call
    this to remove the wrapping.
    """
    if (
            getattr(sys.setrecursionlimit, '__wrapped__', None) and
            getattr(sys.getrecursionlimit, '__wrapped__', None)
    ):
        sys.setrecursionlimit = sys.setrecursionlimit.__wrapped__
        sys.getrecursionlimit = sys.getrecursionlimit.__wrapped__
        sys.setrecursionlimit(sys.getrecursionlimit() - RECURSIONLIMIT_DELTA)


class MyRPCServer(rpc.RPCServer):
    "The subprocess's RPCServer: a dropped link interrupts main and exits."

    def handle_error(self, request, client_address):
        """Override RPCServer method for PEM

        Interrupt the MainThread and exit server if link is dropped.

        """
        global quitting
        try:
            raise
        except SystemExit:
            raise
        except EOFError:
            global exit_now
            exit_now = True
            thread.interrupt_main()
        except:
            erf = sys.__stderr__
            print(textwrap.dedent(f"""
            {'-'*40}
            Unhandled exception in user code execution server!'
            Thread: {threading.current_thread().name}
            PEM Client Address: {client_address}
            Request: {request!r}
            """), file=erf)
            traceback.print_exc(limit=-20, file=erf)
            print(textwrap.dedent(f"""
            *** Unrecoverable, server exiting!

            Users should never see this message; it is likely transient.
            If this recurs, report this with a copy of the message
            and an explanation of how to make it repeat.
            {'-'*40}"""), file=erf)
            quitting = True
            thread.interrupt_main()


# sys.stdin / sys.stdout / sys.stderr in the subprocess are these file-like
# objects; every read/write is an RPC call to the shell.  (pyshell imports them
# too, for the no-subprocess fallback.)

class StdioFile(io.TextIOBase):
    "Base for the RPC-backed stdio proxies; ``shell`` is the remote shell proxy."

    def __init__(self, shell, tags, encoding='utf-8', errors='strict'):
        self.shell = shell
        # GH-78889: accessing unpickleable attributes freezes Shell.
        # PEM only needs methods; allow 'width' for possible use.
        self.shell._RPCProxy__attributes = {'width': 1}
        self.tags = tags
        self._encoding = encoding
        self._errors = errors

    @property
    def encoding(self):
        return self._encoding

    @property
    def errors(self):
        return self._errors

    @property
    def name(self):
        return '<%s>' % self.tags

    def isatty(self):
        return True


class StdOutputFile(StdioFile):
    "sys.stdout / sys.stderr in the subprocess: each write() is an RPC to the shell."

    def writable(self):
        return True

    def write(self, s):
        if self.closed:
            raise ValueError("write to closed file")
        s = str.encode(s, self.encoding, self.errors).decode(self.encoding, self.errors)
        # If ``self.shell`` is an RPCProxy (the normal case, subprocess writing
        # to the GUI), fire-and-forget the write so we don't block on the
        # roundtrip -- the GUI's PyShell.write_subprocess buffers internally.
        # If ``self.shell`` is the GUI's PyShell itself (the no-subprocess
        # fallback, and the internal ``self.console.write(...)`` for prompts),
        # there's no RPC and we just call .write() directly for synchronous
        # immediate rendering.
        sockio = getattr(self.shell, 'sockio', None)
        if sockio is not None:
            try:
                sockio.asynccall_noreturn(
                    self.shell.oid, 'write_subprocess', (s, self.tags), {})
            except OSError:
                return 0
            return len(s)
        try:
            return self.shell.write(s, self.tags) or len(s)
        except Exception:
            return 0


class StdInputFile(StdioFile):
    "sys.stdin in the subprocess: read()/readline() pull lines from the shell via RPC."
    _line_buffer = ''

    def readable(self):
        return True

    def read(self, size=-1):
        if self.closed:
            raise ValueError("read from closed file")
        if size is None:
            size = -1
        elif not isinstance(size, int):
            raise TypeError('must be int, not ' + type(size).__name__)
        result = self._line_buffer
        self._line_buffer = ''
        if size < 0:
            while line := self.shell.readline():
                result += line
        else:
            while len(result) < size:
                line = self.shell.readline()
                if not line: break
                result += line
            self._line_buffer = result[size:]
            result = result[:size]
        return result

    def readline(self, size=-1):
        if self.closed:
            raise ValueError("read from closed file")
        if size is None:
            size = -1
        elif not isinstance(size, int):
            raise TypeError('must be int, not ' + type(size).__name__)
        line = self._line_buffer or self.shell.readline()
        if size < 0:
            size = len(line)
        eol = line.find('\n', 0, size)
        if eol >= 0:
            size = eol + 1
        self._line_buffer = line[size:]
        return line[:size]

    def close(self):
        self.shell.close()


class MyHandler(rpc.RPCHandler):
    "The subprocess end of the RPC link."

    def handle(self):
        "Bind sys.stdin/out/err to the shell, register the 'exec' target, then serve."
        executive = Executive(self)
        self.register("exec", executive)
        self.console = self.get_remote_proxy("console")
        sys.stdin = StdInputFile(self.console, "stdin", encoding, errors)
        sys.stdout = StdOutputFile(self.console, "stdout", encoding, errors)
        sys.stderr = StdOutputFile(self.console, "stderr", encoding,
                                   "backslashreplace")

        sys.displayhook = rpc.displayhook
        # page help() text to shell.
        import pydoc # import must be done here to capture i/o binding
        pydoc.pager = pydoc.plainpager

        # Keep a reference to stdin so that it won't try to exit PEM if
        # sys.stdin gets changed from within PEM's shell. See issue17838.
        self._keep_stdin = sys.stdin

        install_recursionlimit_wrappers()

        self.interp = self.get_remote_proxy("interp")
        perflog.mark("subprocess: RPC handler ready, stdio bound, entering getresponse loop")
        rpc.RPCHandler.getresponse(self, myseq=None, wait=0.05)

    def exithook(self):
        "override SocketIO method - wait for MainThread to shut us down"
        time.sleep(10)

    def EOFhook(self):
        "Override SocketIO method - terminate wait on callback and exit thread"
        global quitting
        quitting = True
        thread.interrupt_main()

    def decode_interrupthook(self):
        "interrupt awakened thread"
        global quitting
        quitting = True
        thread.interrupt_main()


class Executive:
    "The 'exec' RPC target: runs user code (runcode) and relays Ctrl-C interrupts."

    def __init__(self, rpchandler):
        self.rpchandler = rpchandler
        if pem.testing is False:
            self.locals = __main__.__dict__
        else:
            self.locals = {}

    def runcode(self, code):
        global interruptable
        perflog.mark("subprocess: Executive.runcode begin")
        try:
            self.user_exc_info = None
            interruptable = True
            try:
                exec(code, self.locals)
            finally:
                interruptable = False
                perflog.mark("subprocess: Executive.runcode exec returned")
        except SystemExit as e:
            if e.args:  # SystemExit called with an argument.
                ob = e.args[0]
                if not isinstance(ob, (type(None), int)):
                    print('SystemExit: ' + str(ob), file=sys.stderr)
            # Return to the interactive prompt.
        except:
            self.user_exc_info = sys.exc_info()  # For testing, hook, viewer.
            if quitting:
                exit()
            if sys.excepthook is sys.__excepthook__:
                print_exception()
            else:
                try:
                    sys.excepthook(*self.user_exc_info)
                except:
                    self.user_exc_info = sys.exc_info()  # For testing.
                    print_exception()
        else:
            flush_stdout()

    def interrupt_the_server(self):
        if interruptable:
            thread.interrupt_main()


if __name__ == '__main__':
    from unittest import main
    main('pem.pem_test.test_run', verbosity=2)

capture_warnings(False)  # Make sure turned off; see bpo-18081.
