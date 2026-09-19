#######################################################################################
# GuiHandler.py    Version 1.0    12-Mar-2026
# Taj Ballinger, Bill Manaris
#######################################################################################
#
# This file is part of PythonMusic.
#
# PythonMusic is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PythonMusic is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PythonMusic.  If not, see <https://www.gnu.org/licenses/>.
#
# PythonMusic derives from JythonMusic (https://jythonmusic.me),
# Copyright (C) 2011-2023 Bill Manaris, John-Anthony Thevos, Marge Marshall,
# Chris Benson, and Kenneth Hanson.
# Modifications Copyright (C) 2025 Dr. Bill Manaris and the PythonMusic contributors.
#
#######################################################################################
#
# REVISIONS:
#
# 1.0   12-Mar-2026 (tb)   Initial implementation.
# 
#######################################################################################
#
# GuiHandler runs in the main PythonMusic process.
# It manages the GuiRenderer child process, delivers commands to Qt, and
# receives responses and events in return.
#
# This file contains no Qt code and never imports PySide6.
# All Qt activity lives in GuiRenderer.py, which runs in the child process.
#
# See GuiRenderer.py for the full protocol description.
#

import multiprocessing
import threading
import queue
import atexit
import os
import sys
import socket
from pathlib import Path

# Sender thread tick rate.  High enough that the final partial batch after a
# burst (e.g. a tight for loop) reaches Qt within a few milliseconds.
_FLUSH_RATE      = 200
_MAX_BUFFER_SIZE = 512   # flush inline when buffer reaches this size

# Kernel buffer size (bytes) for each end of the command pipe, macOS/Linux only.  The
# macOS default is far smaller than one full command batch, so every send would block
# until the renderer next reads, making the two processes take turns instead of working
# in parallel.  Large enough to hold many batches, small enough that the parent can't run
# far ahead of what's on screen.  (Linux caps the request at net.core.wmem_max/rmem_max.)
_PIPE_BUFFER_SIZE = 1024 * 1024

# Maximum time (seconds) GuiHandler.__init__ will wait for the child to send
# its READY handshake before giving up and raising a diagnostic error.
_READY_TIMEOUT = 5.0


def _logPath():
   """Per-platform path to the GuiRenderer stderr log file.

   Captures both Python tracebacks and C-level output from Qt/Cocoa/XPC so
   child-process failures are diagnosable after the fact.  Creates the parent
   directory if needed.  Returns a pathlib.Path.
   """
   if sys.platform == 'darwin':
      base = Path.home() / "Library" / "Logs" / "PythonMusic"
   elif sys.platform == 'win32':
      base = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / "PythonMusic" / "Logs"
   else:
      stateHome = os.environ.get('XDG_STATE_HOME') or str(Path.home() / ".local" / "state")
      base = Path(stateHome) / "PythonMusic" / "logs"
   try:
      base.mkdir(parents=True, exist_ok=True)
   except OSError:
      pass
   return base / "gui-renderer.log"

#######################################################################################
# Message Protocol Helpers
#
# Plain-dict message constructors shared by GuiHandler (parent) and GuiRenderer (child).
# Keeping them here avoids any import of Qt in the parent process — GuiRenderer imports
# these helpers from this file, not the other way around.
#######################################################################################

def _enlargePipeBuffers(connection):
   """
   Raises the send and receive buffer sizes of one end of a duplex Pipe to
   _PIPE_BUFFER_SIZE.  On macOS/Linux a duplex Pipe is a Unix socket pair, so this is a
   socket option on the underlying file descriptor.  Windows uses named pipes, which
   this doesn't apply to, so they are left at their defaults.
   """
   if sys.platform != 'win32':
      # fromfd() works on a duplicate descriptor; the option applies to the shared socket
      with socket.fromfd(connection.fileno(), socket.AF_UNIX, socket.SOCK_STREAM) as pipeSocket:
         pipeSocket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, _PIPE_BUFFER_SIZE)
         pipeSocket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, _PIPE_BUFFER_SIZE)

def _createCommand(action, target, args=None, responseId=None):
   """
   Creates a command message dict (PythonMusic -> Qt).
   """
   return {
      'action':     action,
      'target':     target,
      'args':       args if args is not None else {},
      'responseId': responseId
   }

def _createResponse(responseId, values=None):
   """
   Creates a response message dict (Qt -> PythonMusic).
   """
   return {
      'responseId': responseId,
      'values':     values if values is not None else []
   }

def _createEvent(eventType, target, args=None):
   """
   Creates an event message dict (Qt -> PythonMusic).
   """
   return {
      'type':   eventType,
      'target': target,
      'args':   args if args is not None else {}
   }


#######################################################################################
# Child process entry point
#######################################################################################

def _launchRenderer(childCommandConnection, childPriorityConnection, parentPriorityConnection):
   """
   Entry point for the GuiRenderer child process.
   Defined here so GuiHandler can reference it without importing from GuiRenderer
   globally (which would also import Qt/PySide6 in the parent process).

   childPriorityConnection is the child end of the duplex admin pipe; the child watches it
   with QSocketNotifier.  Admin commands (setRate, getRate) arrive here, bypassing
   the command buffer.  When the parent closes its end (parentPriorityConnection), the child
   receives EOF and initiates shutdown.

   parentPriorityConnection is the parent's end; the child closes it immediately so that
   only the parent holds it — ensuring the child sees EOF when the parent closes.

   At runtime this function only executes in the child process.
   """
   import traceback

   parentPriorityConnection.close()   # child must not hold the parent end open

   # Redirect fd 2 (stderr) to a per-launch log file so Python tracebacks and
   # C-level output from Qt/Cocoa/XPC are both captured.  Each launch starts
   # fresh and the previous run is preserved as <log>.prev; empty logs are
   # removed on clean exit so successful runs leave no clutter.
   logPath  = _logPath()
   prevPath = logPath.with_suffix(logPath.suffix + ".prev")
   logFile  = None
   try:
      if logPath.exists():
         try:
            if prevPath.exists():
               prevPath.unlink()
            logPath.rename(prevPath)
         except OSError:
            pass
      logFile = open(logPath, "w")
   except OSError:
      # Log path unavailable (sandboxed FS, full disk, etc.) — fall back to
      # /dev/null so the child can still run, just without diagnostics.
      logFile = open(os.devnull, "w")
      logPath = None

   os.dup2(logFile.fileno(), 2)
   sys.stderr = logFile

   try:
      from PythonMusic.GuiRenderer import GuiRenderer
      renderer = GuiRenderer(childCommandConnection, childPriorityConnection)
      renderer.run()
   except Exception:
      traceback.print_exc()
      raise
   finally:
      logFile.flush()
      if logPath is not None:
         try:
            if logPath.exists() and logPath.stat().st_size == 0:
               logFile.close()
               logPath.unlink()
         except OSError:
            pass


# Pin __module__ so spawn's pickle reference resolves to PythonMusic.GuiHandler
# in the child even when this file was loaded as __main__ in the parent (the
# test harness at the bottom does this).
_launchRenderer.__module__ = 'PythonMusic.GuiHandler'


#######################################################################################
# GuiHandler
#######################################################################################

class GuiHandler:
   """
   Runs in the main PythonMusic process.
   Manages the GuiRenderer child process, sends commands, and receives
   responses and events.  Instantiated once as the module-level singleton
   _GUI_HANDLER when gui.py is imported; never exposed directly to the user.
   """

   def __init__(self):
      """
      Spawns the GuiRenderer child process and establishes the IPC Pipe.
      Starts a background listener thread that routes incoming messages to
      waiting sendQuery() callers or registered event callbacks.
      Registers an atexit handler so the child is always cleaned up when
      the parent process exits — no cleanup code required in gui.py.
      """
      parentCommandConnection, childCommandConnection = multiprocessing.Pipe(duplex=True)
      self.connection = parentCommandConnection
      _enlargePipeBuffers(parentCommandConnection)
      _enlargePipeBuffers(childCommandConnection)   # before spawn, so the child's end keeps it

      # spawn everywhere except Linux dev.  Each PythonMusic interpreter spawns
      # exactly one Qt child, so the forkserver/fork speedup has nothing to
      # amortise; spawn keeps the process tree minimal and is the only start
      # method available on Windows and inside a frozen build anyway.  Linux
      # uses fork because it's safe (no Cocoa) and slightly faster.
      if sys.platform == 'linux' and not getattr(sys, 'frozen', False):
         ctx = multiprocessing.get_context('fork')
      else:
         ctx = multiprocessing.get_context('spawn')

      # Dedicated duplex admin pipe.  The parent holds parentPriorityConnection; the child
      # holds childPriorityConnection.  Admin commands (setRate, getRate) travel here,
      # bypassing the command buffer entirely.  Closing parentPriorityConnection sends EOF
      # to the child, which Qt detects via QSocketNotifier and treats as shutdown —
      # independent of the command queue and independent of whether atexit runs.
      childPriorityConnection, parentPriorityConnection = multiprocessing.Pipe(duplex=True)
      self._adminConn = parentPriorityConnection

      # multiprocessing's spawn bootstrap captures __main__.__file__ /
      # __spec__ from the parent and re-imports that module in the child.
      # When the parent IS a user script (run under PEM, or via `python
      # foo.py`), that re-import re-runs the script — any top-level error
      # then crashes the renderer before _launchRenderer is reached.
      # Clear both attributes across the spawn so the child stays clean.
      _main_mod   = sys.modules.get('__main__')
      _saved_file = getattr(_main_mod, '__file__', _UNSET := object())
      _saved_spec = getattr(_main_mod, '__spec__', _UNSET)
      if _main_mod is not None:
         _main_mod.__file__ = None
         _main_mod.__spec__ = None
      try:
         self.childProcess = ctx.Process(
            target = _launchRenderer,
            args   = (childCommandConnection, childPriorityConnection, parentPriorityConnection),
            daemon = True   # child is killed automatically if parent dies unexpectedly
         )
         self.childProcess.start()
      finally:
         if _main_mod is not None:
            if _saved_file is not _UNSET:
               _main_mod.__file__ = _saved_file
            if _saved_spec is not _UNSET:
               _main_mod.__spec__ = _saved_spec
      childCommandConnection.close()      # parent no longer needs the child end of the command pipe
      childPriorityConnection.close() # parent no longer needs the child end of the admin pipe

      # READY handshake.  The child sends {'type': 'ready'} once Qt is fully
      # wired up.  Consume it here, before the listener thread starts, so the
      # message isn't routed as an event.  A timeout means the child crashed
      # during initialization; the diagnostic points at the stderr log.
      try:
         if not self.connection.poll(timeout=_READY_TIMEOUT):
            self._abortStartup(
               f"PythonMusic GUI subprocess did not send READY within "
               f"{_READY_TIMEOUT}s.  This usually means Qt failed to "
               f"initialize in the child process.  See child stderr log at: "
               f"{_logPath()}"
            )
         readyMessage = self.connection.recv()
      except (EOFError, OSError) as e:
         self._abortStartup(
            f"PythonMusic GUI subprocess died during startup "
            f"({type(e).__name__}).  See child stderr log at: {_logPath()}",
            cause=e,
         )
      if not (isinstance(readyMessage, dict) and readyMessage.get('type') == 'ready'):
         self._abortStartup(
            f"PythonMusic GUI subprocess sent unexpected handshake message: "
            f"{readyMessage!r}.  See child stderr log at: {_logPath()}"
         )

      # responseId counter — each sendQuery() call gets a unique ID so the
      # listener thread can route the response back to the correct caller
      self._responseIdCount = 0
      self._responseIdLock  = threading.Lock()

      # pending responses — maps responseId -> {'event': threading.Event, 'values': list}
      # sendQuery() registers a slot here before sending, then blocks on the Event.
      # The listener thread writes values into the slot and signals the Event.
      self._pendingResponses = {}
      self._pendingLock      = threading.Lock()

      # event registry — maps (objectId, eventType) -> callback function
      # Populated by registerEvent(); consulted by the listener thread on each event.
      self._eventRegistry = {}

      # send lock — Pipe.send() is not thread-safe; all outgoing messages
      # must acquire this lock before writing to the pipe
      self._sendLock = threading.Lock()

      # command buffer — fire-and-forget commands are queued here and sent as
      # a single batch by the sender thread (or flushed early on a query)
      self._commandBuffer = []
      self._bufferLock    = threading.Lock()

      # flush rate - how often to flush the buffer
      self._flushRate     = _FLUSH_RATE
      self._maxBufferSize = _MAX_BUFFER_SIZE

      # callback active lock — held by the dispatch thread while an event callback
      # is executing.  The sender thread checks this non-blocking; if it can't
      # acquire, it skips that flush tick so mid-callback commands don't travel as
      # a partial batch.  After the callback, the dispatch thread does one explicit
      # flush to send everything the callback accumulated as a single pipe message.
      self._callbackActive = threading.Lock()

      # sender thread — wakes every 1/FLUSH_RATE seconds and flushes the buffer
      self._senderStopEvent = threading.Event()
      self._senderThread = threading.Thread(
         target = self._runSenderThread,
         daemon = True
      )
      self._senderThread.start()

      # event queue — listener thread enqueues incoming events here; dispatch
      # thread drains it and runs callbacks.  Decoupling the two threads means
      # callbacks can call sendQuery() without deadlocking the listener.
      self._eventQueue = queue.SimpleQueue()

      # single listener thread handles both responses and events, since both
      # arrive on the same connection and reading from it on two threads would race
      self._listenerThread = threading.Thread(
         target = self._listenForMessages,
         daemon = True
      )
      self._listenerThread.start()

      # dispatch thread runs event callbacks sequentially off the event queue,
      # keeping the listener thread free to receive query responses at all times
      self._dispatchThread = threading.Thread(
         target = self._runDispatchThread,
         daemon = True
      )
      self._dispatchThread.start()

      atexit.register(self._shutdown)

   # ── Startup helpers ───────────────────────────────────────────────────────

   def _abortStartup(self, message, cause=None):
      """
      Called when the READY handshake fails.  Terminates the child if it's still
      alive, then raises RuntimeError with a diagnostic message.  Used only
      during __init__; never called after the listener thread is running.
      """
      try:
         if self.childProcess.is_alive():
            self.childProcess.terminate()
            self.childProcess.join(timeout=1.0)
      except Exception:
         pass
      if cause is not None:
         raise RuntimeError(message) from cause
      raise RuntimeError(message)

   # ── Response ID ───────────────────────────────────────────────────────────

   def _nextResponseId(self):
      """
      Returns the next unique responseId.  Thread-safe.
      """
      with self._responseIdLock:
         self._responseIdCount += 1
         return self._responseIdCount

   # ── Listener thread ───────────────────────────────────────────────────────

   def _listenForMessages(self):
      """
      Background thread.  Reads incoming messages from GuiRenderer and routes
      each one: responses unblock waiting sendQuery() callers; events are
      pushed onto _eventQueue for the dispatch thread.  Exits when the child
      closes the pipe (EOFError), releases any waiting sendQuery() callers,
      and sends a None sentinel to stop the dispatch thread.
      """
      while True:
         try:
            message = self.connection.recv()
            if 'responseId' in message:
               self._handleResponse(message)
            elif 'type' in message:
               self._eventQueue.put(message)
         except EOFError:
            break
      with self._pendingLock:
         for slot in self._pendingResponses.values():
            slot['values'] = ['shutdown']
            slot['event'].set()
      self._eventQueue.put(None)   # sentinel: tell dispatch thread to stop

   def _handleResponse(self, responseDict):
      """
      Routes an incoming response to the sendQuery() call that is waiting for it.
      Called from the listener thread.
      """
      responseId = responseDict.get('responseId')
      values     = responseDict.get('values', [])

      with self._pendingLock:
         pendingSlot = self._pendingResponses.get(responseId)

      if pendingSlot is not None:
         pendingSlot['values'] = values   # store result before signalling
         pendingSlot['event'].set()       # unblock the waiting sendQuery() call

   # ── Sender thread ─────────────────────────────────────────────────────────

   def _runSenderThread(self):
      """
      Background thread.  Wakes every 1 / _flushRate seconds and flushes the
      command buffer.  Skips a tick if a callback is currently executing
      (_callbackActive is held) so the callback's commands don't get split
      across multiple pipe messages.  Exits when _senderStopEvent is set.
      """
      while not self._senderStopEvent.wait(timeout=1.0 / self._flushRate):
         if self._callbackActive.acquire(blocking=False):
            self._callbackActive.release()
            self._flushBuffer()
         # else: callback in progress — skip this tick
      self._flushBuffer()   # final drain on shutdown

   def _flushBuffer(self):
      """
      Sends the current command buffer as a single batch message, then resets
      the buffer.  Thread-safe; concurrent callers are safe — only one will
      get a non-empty batch, the others are no-ops.
      """
      with self._bufferLock:
         batch = self._commandBuffer
         if not batch:
            return
         self._commandBuffer = []
      with self._sendLock:
         try:
            self.connection.send(batch)
         except (BrokenPipeError, OSError):
            self._senderStopEvent.set()   # pipe is gone; stop the sender thread

   def getFlushRate(self):
      """
      Returns the current tick rate for flushing the command buffer.
      """
      return self._flushRate

   def setFlushRate(self, flushRate):
      """
      Sets the current tick rate for flushing the command buffer.
      """
      self._flushRate = flushRate

   def getRate(self):
      """
      Returns the current render rate (timer ticks per second) of the Qt renderer.
      Sends directly on the admin pipe, bypassing the command buffer.
      """
      self._adminConn.send({'action': 'getRate'})
      return self._adminConn.recv()

   def setRate(self, rate):
      """
      Sets the render rate (timer ticks per second) of the Qt renderer.
      Sends directly on the admin pipe, bypassing the command buffer.
      """
      self._adminConn.send({'action': 'setRate', 'rate': rate})

   # ── Sending ───────────────────────────────────────────────────────────────

   def sendCommand(self, action, target, args=None):
      """
      Queues a fire-and-forget command in the command buffer.  The sender thread
      flushes on each tick.  Thread-safe.

      Back-to-back commands with the same action, target, and arg names are merged
      into one 'merged' command (see _appendCommand), so a tight loop of small commands
      (e.g. drawPoint, setPixel) is cheap to send.  A run holds at most _maxBufferSize
      commands, the same limit as the buffer itself.
      """
      with self._bufferLock:
         runLength = self._appendCommand(action, target, args)
         flush_now = (len(self._commandBuffer) >= self._maxBufferSize
                      or runLength >= self._maxBufferSize)
      if flush_now and self._callbackActive.acquire(blocking=False):
         self._callbackActive.release()
         self._flushBuffer()

   def _appendCommand(self, action, target, args):
      """
      Adds a command to the buffer, merging it with the buffer's last command when both
      have the same action, target, and arg names.  A merged command stores the arg names
      once and each command's arg values as a tuple:

         {'action': 'merged', 'target': target,
          'args': {'action': action, 'argNames': (...), 'rows': [(...), (...), ...]}}

      That is far cheaper to pickle than one dict per command, and lets the renderer
      handle the whole run at once (see GuiRenderer._executeMerged).  Order is kept,
      since only neighbors merge.  A lone command is left in its normal form; it becomes
      a run only when a matching command arrives right behind it.

      Caller holds _bufferLock.  Returns the length of the run the command is in (1 if
      it was not merged).
      """
      if args is None:
         args = {}
      argNames = tuple(args)

      lastCommand = self._commandBuffer[-1] if self._commandBuffer else None
      runLength   = 1

      if lastCommand is not None and lastCommand['target'] == target:
         lastArgs = lastCommand['args']

         extendsRun = (lastCommand['action'] == 'merged'
                       and lastArgs['action']   == action
                       and lastArgs['argNames'] == argNames)
         startsRun  = (lastCommand['action'] == action
                       and tuple(lastArgs) == argNames)

         if extendsRun:
            lastArgs['rows'].append(tuple(args.values()))
            runLength = len(lastArgs['rows'])
         elif startsRun:
            # the second matching command: turn the last command into a run of two
            self._commandBuffer[-1] = _createCommand('merged', target, {
               'action':   action,
               'argNames': argNames,
               'rows':     [tuple(lastArgs.values()), tuple(args.values())],
            })
            runLength = 2

      if runLength == 1:
         self._commandBuffer.append(_createCommand(action, target, args))
      return runLength

   def sendQuery(self, action, target, args=None):
      """
      Sends a command to GuiRenderer and blocks until a response is received.
      Returns the response's values list.  Thread-safe; multiple callers may
      block concurrently — each is matched to its response by responseId.

      Flushes any buffered fire-and-forget commands before sending the query
      so that GuiRenderer processes them first and the query reflects up-to-date
      state.  The flush and query send are both performed under _sendLock so
      no other thread can interleave a send between them.
      """
      responseId  = self._nextResponseId()
      pendingSlot = {'event': threading.Event(), 'values': None}

      # register the slot before sending so the listener never misses the response
      with self._pendingLock:
         self._pendingResponses[responseId] = pendingSlot

      command = _createCommand(action, target, args, responseId=responseId)

      # grab any buffered commands, then send them + the query atomically as one list
      with self._bufferLock:
         batch = self._commandBuffer
         self._commandBuffer = []
      with self._sendLock:
         try:
            self.connection.send(batch + [command])
         except (BrokenPipeError, OSError):
            pass   # pipe is gone; listener thread will release the pending slot via EOFError

      pendingSlot['event'].wait()   # block until the listener signals a response

      with self._pendingLock:
         del self._pendingResponses[responseId]   # clean up the slot

      return pendingSlot['values']

   # ── Events ────────────────────────────────────────────────────────────────

   def registerEvent(self, objectId, eventType, callback):
      """
      Registers a callback for a specific event type on a specific object.
      Stores the callback locally and notifies GuiRenderer to watch for the
      corresponding Qt event on that object.
      When GuiRenderer sends a matching event, the callback is invoked with
      the event's args dict unpacked as keyword arguments.
      """
      self._eventRegistry[(objectId, eventType)] = callback

      registrationArgs = {'objectId': objectId, 'eventType': eventType}
      self.sendCommand('registerEvent', None, registrationArgs)

   def _runDispatchThread(self):
      """
      Background thread.  Drains _eventQueue and runs event callbacks
      sequentially.  Decoupled from the listener thread so callbacks can call
      sendQuery() without deadlocking the listener.

      Coalesces consecutive position events (mouseMove, mouseDrag) for the same
      target: when multiple are queued back-to-back, only the last one is
      dispatched.  This prevents lag when a callback involves a query round-trip
      (e.g. intersects()) that causes events to accumulate faster than they are
      consumed.  All other event types (clicks, keys, enter/exit) are always
      dispatched in full order.

      Exits when it receives the None sentinel pushed by _listenForMessages.
      """
      _COALESCE = frozenset({'mouseMove', 'mouseDrag'})

      while True:
         # block until at least one event is available
         batch = [self._eventQueue.get()]
         if batch[0] is None:
            break

         # drain any additional immediately-available events into the batch
         try:
            while True:
               msg = self._eventQueue.get(block=False)
               batch.append(msg)
               if msg is None:
                  break   # sentinel — process batch then exit
         except queue.Empty:
            pass

         # process the batch in order, coalescing consecutive position events
         i = 0
         while i < len(batch):
            msg = batch[i]
            if msg is None:
               return   # sentinel reached mid-batch

            eventType = msg.get('type')
            if eventType in _COALESCE:
               target = msg.get('target')
               # find the last consecutive event of the same type+target
               j = i + 1
               while (j < len(batch)
                      and batch[j] is not None
                      and batch[j].get('type')   == eventType
                      and batch[j].get('target') == target):
                  j += 1
               with self._callbackActive:
                  self._dispatchEvent(batch[j - 1])   # skip stale positions
               self._flushBuffer()
               i = j
            else:
               with self._callbackActive:
                  self._dispatchEvent(msg)
               self._flushBuffer()
               i += 1

   def _dispatchEvent(self, eventDict):
      """
      Looks up and calls the callback registered for the incoming event.
      Called from the dispatch thread.
      """
      eventType = eventDict.get('type')
      objectId  = eventDict.get('target')
      args      = eventDict.get('args', {})

      callback = self._eventRegistry.get((objectId, eventType))
      if callback is not None and callable(callback):
         if isinstance(args, list):
            callback(*args)
         else:
            callback(**args)

   # ── Shutdown ──────────────────────────────────────────────────────────────

   def _shutdown(self):
      """
      Signals the child to shut down and waits for it to exit.
      Stops the sender thread first so any remaining buffered commands are
      flushed before the pipe closes.  Closing the shutdown pipe delivers EOF
      to the child's QSocketNotifier, which fires _onShutdownSignal on Qt's
      main thread immediately — even if atexit does not run, since the OS
      closes the pipe fd on process death.
      Called automatically via atexit when the parent process exits.
      """
      self._senderStopEvent.set()
      self._senderThread.join(timeout=1.0)
      self._adminConn.close()   # EOF on child's admin pipe triggers shutdown
      self.childProcess.join(timeout=1.0)


#######################################################################################
# Handler factory
#######################################################################################

class _NullHandler:
   """
   Stub returned by _createHandler() when called from a spawn-context child
   re-importing __main__.  Top-level Display / shape creation in the user's
   script would otherwise run a second time during that re-import and either
   crash or spawn another renderer.  This stub absorbs all calls silently.
   """
   def sendCommand(self, action, target, args=None): pass
   def sendQuery(self,   action, target, args=None): return [0, 0, 0, 0]
   def registerEvent(self, objectId, eventType, callback): pass
   def getFlushRate(self): return _FLUSH_RATE
   def setFlushRate(self, flushRate): pass
   def getRate(self): return _FLUSH_RATE
   def setRate(self, _rate): pass


def _createHandler():
   """
   Returns a GuiHandler in the main process; returns _NullHandler in any
   child process re-importing __main__ during multiprocessing bootstrap.
   """
   if multiprocessing.parent_process() is not None:
      return _NullHandler()
   multiprocessing.freeze_support()
   return GuiHandler()


#######################################################################################
# Phase 4 Test
#######################################################################################

def _runPhase4Test():
   """Phase 4 GuiHandler/GuiRenderer smoke test.  Run via the __main__ block
   below, which delegates here through a re-import so spawn sees one module
   identity for _launchRenderer.
   """
   import time

   PASS = '\033[92m✓\033[0m'
   FAIL = '\033[91m✗\033[0m'

   def check(label, condition):
      print(f'  {PASS if condition else FAIL}  {label}')
      if not condition:
         raise AssertionError(f'FAILED: {label}')

   print()
   print('GuiHandler / GuiRenderer — Phase 4 Test')
   print('=' * 40)
   print('  (A small window will appear briefly during this test.)')

   handler = GuiHandler()   # blocks until the child sends READY

   DISPLAY_ID = 1   # objectId used for the test Display

   # ── Create Display ────────────────────────────────────────────────────────
   print('\n[1] Create Display')

   createArgs = {
      'type':   'Display',
      'title':  'Phase 4 Test',
      'width':  300,
      'height': 200,
      'x':      100,
      'y':      100,
      'color':  [255, 255, 255, 255]   # white
   }
   handler.sendCommand('create', DISPLAY_ID, createArgs)
   time.sleep(0.2)   # allow Qt to create and show the window

   pingResult = handler.sendQuery('ping', None)
   check('Qt event loop alive after create', pingResult == ['pong'])

   # ── Query initial state ───────────────────────────────────────────────────
   print('\n[2] Query initial state')

   titleResult = handler.sendQuery('getTitle', DISPLAY_ID)
   check('getTitle returns "Phase 4 Test"', titleResult == ['Phase 4 Test'])

   sizeResult = handler.sendQuery('getSize', DISPLAY_ID)
   check('getSize returns [300, 200]', sizeResult == [300, 200])

   widthResult = handler.sendQuery('getWidth', DISPLAY_ID)
   check('getWidth returns 300', widthResult == [300])

   heightResult = handler.sendQuery('getHeight', DISPLAY_ID)
   check('getHeight returns 200', heightResult == [200])

   colorResult = handler.sendQuery('getColor', DISPLAY_ID)
   check('getColor returns [255, 255, 255, 255]', colorResult == [255, 255, 255, 255])

   posResult = handler.sendQuery('getPosition', DISPLAY_ID)
   check('getPosition returns two integers',
         len(posResult) == 2 and all(isinstance(v, int) for v in posResult))

   # ── Setters round-trip ────────────────────────────────────────────────────
   print('\n[3] Setters round-trip')

   handler.sendCommand('setTitle', DISPLAY_ID, {'title': 'Updated Title'})
   titleResult2 = handler.sendQuery('getTitle', DISPLAY_ID)
   check('setTitle → getTitle round-trips', titleResult2 == ['Updated Title'])

   handler.sendCommand('setColor', DISPLAY_ID, {'color': [0, 0, 255, 255]})
   colorResult2 = handler.sendQuery('getColor', DISPLAY_ID)
   check('setColor → getColor round-trips', colorResult2 == [0, 0, 255, 255])

   handler.sendCommand('setSize', DISPLAY_ID, {'width': 400, 'height': 300})
   sizeResult2 = handler.sendQuery('getSize', DISPLAY_ID)
   check('setSize → getSize round-trips', sizeResult2 == [400, 300])

   handler.sendCommand('setPosition', DISPLAY_ID, {'x': 150, 'y': 150})
   posResult2 = handler.sendQuery('getPosition', DISPLAY_ID)
   check('setPosition returns two integers',
         len(posResult2) == 2 and all(isinstance(v, int) for v in posResult2))

   # ── Visibility ────────────────────────────────────────────────────────────
   print('\n[4] Visibility')

   handler.sendCommand('hide', DISPLAY_ID)
   time.sleep(0.1)
   check('Qt alive after hide', handler.sendQuery('ping', None) == ['pong'])

   handler.sendCommand('show', DISPLAY_ID)
   time.sleep(0.1)
   check('Qt alive after show', handler.sendQuery('ping', None) == ['pong'])

   time.sleep(5)  # hang for a few seconds to show Display

   # ── displayClose event ────────────────────────────────────────────────────
   print('\n[5] displayClose event')

   closeReceived = []

   def onDisplayClose():
      closeReceived.append(True)

   handler.registerEvent(DISPLAY_ID, 'displayClose', onDisplayClose)
   time.sleep(0.1)

   handler.sendCommand('close', DISPLAY_ID)
   time.sleep(0.2)

   check('displayClose event received', len(closeReceived) == 1)

   # ── Shutdown ──────────────────────────────────────────────────────────────
   print('\n[6] Shutdown')

   handler._shutdown()
   check('child process has exited', not handler.childProcess.is_alive())

   print()
   print('All Phase 4 tests passed.')
   print()


if __name__ == '__main__':
   multiprocessing.freeze_support()
   # Re-import so the test runs against PythonMusic.GuiHandler — not the
   # __main__ copy of this file — which keeps spawn's pickle references
   # resolving to a single module identity.
   from PythonMusic.GuiHandler import _runPhase4Test
   _runPhase4Test()
