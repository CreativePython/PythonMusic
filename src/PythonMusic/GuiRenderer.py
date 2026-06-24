#######################################################################################
# GuiRenderer.py    Version 1.0    12-Mar-2026
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
# GuiRenderer runs in the child process and owns the Qt event loop.
# It receives commands from GuiHandler via a Pipe, renders them with Qt,
# and sends back responses and events.
#
# This file is never imported by gui.py — only by the child process via the lazy
# import inside GuiHandler._launchRenderer().  Qt can therefore be
# imported normally at the top of this file without affecting the main interpreter.
#
# Mirror objects
# --------------
# Each gui.py class that creates Qt objects has a mirror class here
# (e.g. Display -> DisplayMirror, Rectangle -> RectangleMirror).  Mirror objects are
# instantiated by 'create' commands and registered in GuiRenderer._objectRegistry
# under their objectId.  Subsequent commands are dispatched to the mirror by objectId.
#
# Base classes
# ------------
# _DrawableMirror  — position, size, rotation, hit-testing, visibility, tooltip
# _GraphicsMirror  — color, fill, thickness  (extends _DrawableMirror)
# Each concrete shape class extends _GraphicsMirror and may override _setSize.
#
# Command dispatch
# ----------------
# Each mirror class builds a _commandHandlers dict in __init__, mapping action
# names to handler methods.  Handlers always take (args, responseId) so the
# dispatcher (handleCommand) stays uniform.  Because Python resolves 'self.method'
# through the MRO at the time the dict is built, subclass overrides (e.g.
# RectangleMirror._setSize) are picked up automatically without extra wiring.
#
# Event handling
# --------------
# GuiHandler.registerEvent() stores a callback locally and sends a 'registerEvent'
# command here.  GuiRenderer stores the (objectId, eventType) pair in
# _registeredEvents.  The _QtGraphicsItemEventMixin and QtView check _registeredEvents
# before relaying any Qt event across the pipe, so only user-registered events
# generate inter-process traffic.
#
# See GuiHandler.py for the full protocol description.
#

import sys

import PySide6.QtWidgets       as QtWidgets
import PySide6.QtCore          as QtCore
import PySide6.QtGui           as QtGui

from PythonMusic.GuiHandler import _createCommand, _createResponse, _createEvent

# Arc style constants — must match gui.py's PIE, OPEN, CHORD values.
# Defined here to avoid importing gui.py in the child process.
_PIE   = 0
_OPEN  = 1
_CHORD = 2

_RENDER_RATE = 60   # default timer ticks per second


#######################################################################################
# GuiRenderer
#######################################################################################

class GuiRenderer:
   """
   Owns the Qt event loop and all Qt objects in the child process.
   Receives commands from GuiHandler via a Pipe, renders them, and sends
   back responses and events.

   Command routing
   ---------------
   'create' commands instantiate a new mirror object (e.g. DisplayMirror, RectangleMirror)
   and register it in _objectRegistry under the objectId in the command's 'target'
   field.  All subsequent commands for that object are routed to it by objectId.
   Built-in actions ('ping', 'shutdown', 'registerEvent') are handled directly.
   Unknown targets and unknown actions are silently ignored.
   """

   def __init__(self, connection, priorityConnection):
      """
      Creates the QApplication and initializes all registries.
      """
      # Remember the connection pipes
      self.commandConnection  = connection
      self.priorityConnection = priorityConnection

      # QApplication must be created first; it owns the Qt event loop.
      self.qApplication = QtWidgets.QApplication([])

      # Do not quit when the last window is closed — the child stays alive
      # until the parent closes the admin pipe, triggering _receiveAdminMessage.
      self.qApplication.setQuitOnLastWindowClosed(False)

      # flat queue of individual commands waiting to be processed by Qt
      self._commandBuffer = []
      self._renderRate    = _RENDER_RATE

      # maps objectId (int) -> mirror object (e.g. DisplayMirror, RectangleMirror)
      self._objectRegistry = {}

      # set of (objectId, eventType) pairs registered by the parent process.
      # _QtGraphicsItemEventMixin and QtView check this before sending events across the pipe.
      self._registeredEvents = set()

      # DisplayMirrors that received draw calls this tick and need a deferred setPixmap.
      # Populated by DisplayMirror._markDrawLayerDirty(); flushed at the end of
      # _processCommandBuffer so Qt sees one atomic update per tick rather than one
      # per draw primitive.
      self._dirtyDisplays = set()

   def run(self):
      """
      Wires up event sources and enters Qt's event loop.

      On macOS/Linux, QSocketNotifier monitors the command and admin pipes
      directly (any file descriptor is valid there).

      On Windows, QSocketNotifier only supports socket file descriptors —
      anonymous pipes from multiprocessing.Pipe() are not monitored.
      QTimer polling is used instead: the render timer polls the command pipe
      each tick, and a dedicated admin timer polls the admin pipe at 20 Hz.

      _commandListener / render timer: receives batched commands and queues
      them for the render timer to process.

      _adminListener / _adminPollTimer: receives admin commands (setRate,
      getRate) on the dedicated admin pipe.  EOF on the admin pipe triggers
      shutdown.
      """
      if sys.platform != 'win32':
         # QSocketNotifier works with any file descriptor on macOS/Linux.
         self._commandListener = QtCore.QSocketNotifier(
            self.commandConnection.fileno(),
            QtCore.QSocketNotifier.Type.Read
         )
         self._commandListener.activated.connect(self._receiveMessage)

         self._adminListener = QtCore.QSocketNotifier(
            self.priorityConnection.fileno(),
            QtCore.QSocketNotifier.Type.Read
         )
         self._adminListener.activated.connect(self._receiveAdminMessage)

         self._adminPollTimer = None
      else:
         # On Windows, poll both pipes with timers instead.
         self._commandListener = None
         self._adminListener   = None

         self._adminPollTimer = QtCore.QTimer()
         self._adminPollTimer.setInterval(50)  # 20 Hz — sufficient for admin/shutdown
         self._adminPollTimer.timeout.connect(self._pollAdminConnection)
         self._adminPollTimer.start()

      # Render timer — drains _commandBuffer each tick (also polls command
      # pipe on Windows).
      self._renderTimer = QtCore.QTimer()
      self._renderTimer.setInterval(1000 // self._renderRate)
      self._renderTimer.timeout.connect(self._processCommandBuffer)
      self._renderTimer.start()

      # READY handshake — sent after all listeners and timers are wired up so
      # the parent only unblocks once we can actually service commands.
      try:
         self.commandConnection.send({'type': 'ready'})
      except (BrokenPipeError, OSError):
         return   # parent died before handoff

      ### Start Qt's event loop
      self.qApplication.exec()

   # ── Command polling ───────────────────────────────────────────────────────

   def _receiveMessage(self):
      """
      Called by _commandListener when a message arrives on the command pipe.
      Each message is a list of command dicts; all commands are unpacked into
      the flat _commandBuffer for the render timer to drain at its normal rate.
      Queries block the parent until their response is sent, which happens
      naturally when the render timer reaches that command in the queue.
      """
      try:
         message = self.commandConnection.recv()
      except (EOFError, OSError):
         # Command pipe closed — parent process died without sending a shutdown
         # signal (e.g. killed by SIGTERM/SIGKILL, atexit didn't run).
         if self._commandListener is not None:
            self._commandListener.setEnabled(False)
         if self._adminListener is not None:
            self._adminListener.setEnabled(False)
         if self._adminPollTimer is not None:
            self._adminPollTimer.stop()
         self._renderTimer.stop()
         self.qApplication.quit()
         return

      # fallback: wrap bare dict in a list (shouldn't happen in normal operation)
      if isinstance(message, dict):
         message = [message]

      # add received commands to buffer
      self._commandBuffer.extend(message)


   def _pollAdminConnection(self):
      """
      Windows only: called by _adminPollTimer to check the admin pipe for an
      incoming message or EOF.  A single poll per tick is sufficient because
      admin messages (setRate, getRate, shutdown) are infrequent.
      """
      try:
         ready = self.priorityConnection.poll(0)
      except OSError:
         # Pipe is broken (parent died) — treat as EOF and shut down.
         self._receiveAdminMessage()
         return
      if ready:
         self._receiveAdminMessage()

   def _processCommandBuffer(self):
      """
      Called by _renderTimer each tick at a constant _RENDER_RATE.  On Windows,
      also polls the command pipe first (QSocketNotifier cannot monitor pipes
      there).  Processes all available commands each tick at full speed.
      setRate controls how often this fires; visual step size is determined by
      how many commands GuiHandler has sent since the last tick.

      After executing all commands, flushes deferred draw layer updates: each
      DisplayMirror that had draw calls this tick gets exactly one setPixmap
      call, so Qt sees one atomic scene update rather than one per draw primitive.
      """
      if sys.platform == 'win32':
         try:
            while self.commandConnection.poll(0):
               self._receiveMessage()
         except OSError:
            self._receiveMessage()   # will catch the OSError in recv() and shut down

      if not self._commandBuffer:
         return
      batch = self._commandBuffer
      self._commandBuffer = []
      for command in batch:
         try:
            self._executeCommand(command)
         except Exception:
            import traceback
            traceback.print_exc()   # captured by PEM_debug.log via stderr redirect
            responseId = command.get('responseId')
            if responseId is not None:
               self.sendResponse(responseId, [])
      # flush deferred draw layer updates accumulated during this tick
      for display in self._dirtyDisplays:
         display._drawLayer.setPixmap(display._drawPixmap)
      self._dirtyDisplays.clear()


   def _executeCommand(self, command):
      """
      Routes an incoming command to the appropriate handler.
      Shutdown is handled out-of-band by _receiveShutdown; unknown actions are
      silently ignored.
      """
      action     = command.get('action')
      target     = command.get('target')
      args       = command.get('args', {})
      responseId = command.get('responseId')

      # ── Admin Actions ──────────────────────────────────────────────────
      if action == 'ping':
         response = _createResponse(responseId, ['pong'])
         self.commandConnection.send(response)

      elif action == 'registerEvent':
         objectId  = args.get('objectId')
         eventType = args.get('eventType')
         self._registeredEvents.add((objectId, eventType))
         # configure Qt item flags so the item receives the right event types
         mirror = self._objectRegistry.get(objectId)
         if mirror is not None and hasattr(mirror, 'qObject') and mirror.qObject is not None:
            if eventType in ('mouseEnter', 'mouseExit', 'mouseMove'):
               mirror.qObject.setAcceptHoverEvents(True)
            elif eventType in ('keyDown', 'keyUp', 'keyType'):
               focusable = QtWidgets.QGraphicsItem.GraphicsItemFlag.ItemIsFocusable
               mirror.qObject.setFlag(focusable, True)

      elif action == 'unregisterEvent':
         objectId  = args.get('objectId')
         eventType = args.get('eventType')
         self._registeredEvents.discard((objectId, eventType))

      elif action == 'fireTestEvent':
         eventType   = args.get('eventType', 'testEvent')
         eventTarget = args.get('target', 0)
         eventArgs   = args.get('eventArgs', {})
         self.sendEvent(eventType, eventTarget, eventArgs)

      elif action == 'colorDialog':
         import sys, subprocess
         initial = args.get('initial', [0, 0, 0, 255])
         r, g, b, a = initial

         if sys.platform == 'darwin':
            # On macOS, showing any dialog (native or Qt) while a Qt window is
            # on screen triggers Metal blit-shader compilation in Qt's window
            # backing store.  On Apple Silicon (AGXMetalG15X_M1) this compilation
            # aborts at the GPU driver level (SIGABRT), killing the child process.
            #
            # Fix: run the color picker as a completely separate process via
            # osascript.  It has its own Metal context and no interaction with
            # Qt's rendering pipeline.  AppleScript returns 16-bit components
            # (0-65535); we rescale to 8-bit (0-255).
            r16 = int(r / 255 * 65535 + 0.5)
            g16 = int(g / 255 * 65535 + 0.5)
            b16 = int(b / 255 * 65535 + 0.5)
            script = f'choose color default color {{{r16}, {g16}, {b16}}}'
            proc = subprocess.run(['osascript', '-e', script],
                                  capture_output=True, text=True)
            if proc.returncode == 0:
               parts  = proc.stdout.strip().strip('{}').split(', ')
               result = [int(int(p) / 65535 * 255 + 0.5) for p in parts]
            else:
               result = [r, g, b]   # user cancelled
         else:
            # On Windows and Linux, QColorDialog works without issue.
            initialColor = QtGui.QColor(r, g, b, a)
            chosen = QtWidgets.QColorDialog.getColor(initialColor)
            if chosen.isValid():
               result = [chosen.red(), chosen.green(), chosen.blue()]
            else:
               result = [r, g, b]   # user cancelled
         response = _createResponse(responseId, result)
         self.commandConnection.send(response)

      # ── Object Creation ───────────────────────────────────────────────────
      elif action == 'create':
         objectType = args.get('type')
         objectId   = target   # objectId is pre-assigned by the parent process

         if objectType == 'Display':
            mirror = DisplayMirror(objectId, args, self)
            self._objectRegistry[objectId] = mirror

         elif objectType == 'Rectangle':
            mirror = RectangleMirror(objectId, args, self)
            self._objectRegistry[objectId] = mirror

         elif objectType == 'Oval':
            mirror = OvalMirror(objectId, args, self)
            self._objectRegistry[objectId] = mirror

         elif objectType == 'Arc':
            mirror = ArcMirror(objectId, args, self)
            self._objectRegistry[objectId] = mirror

         elif objectType == 'Polyline':
            mirror = PolylineMirror(objectId, args, self)
            self._objectRegistry[objectId] = mirror

         elif objectType == 'Line':
            mirror = LineMirror(objectId, args, self)
            self._objectRegistry[objectId] = mirror

         elif objectType == 'Polygon':
            mirror = PolygonMirror(objectId, args, self)
            self._objectRegistry[objectId] = mirror

         elif objectType == 'Icon':
            mirror = IconMirror(objectId, args, self)
            self._objectRegistry[objectId] = mirror

         elif objectType == 'Label':
            mirror = LabelMirror(objectId, args, self)
            self._objectRegistry[objectId] = mirror

         elif objectType == 'Group':
            mirror = GroupMirror(objectId, args, self)
            self._objectRegistry[objectId] = mirror

         elif objectType == 'Button':
            mirror = ButtonMirror(objectId, args, self)
            self._objectRegistry[objectId] = mirror

         elif objectType == 'CheckBox':
            mirror = CheckBoxMirror(objectId, args, self)
            self._objectRegistry[objectId] = mirror

         elif objectType == 'Slider':
            mirror = SliderMirror(objectId, args, self)
            self._objectRegistry[objectId] = mirror

         elif objectType == 'DropDownList':
            mirror = DropDownListMirror(objectId, args, self)
            self._objectRegistry[objectId] = mirror

         elif objectType == 'TextField':
            mirror = TextFieldMirror(objectId, args, self)
            self._objectRegistry[objectId] = mirror

         elif objectType == 'TextArea':
            mirror = TextAreaMirror(objectId, args, self)
            self._objectRegistry[objectId] = mirror

         elif objectType == 'Menu':
            mirror = MenuMirror(objectId, args, self)
            self._objectRegistry[objectId] = mirror

      # ── Object Commands ─────────────────────────────────────────────
      else:
         # any other commands are defined by their target objects
         # unknown targets are silently ignored
         mirrorObject = self._objectRegistry.get(target)
         if mirrorObject is not None:
            mirrorObject.handleCommand(action, args, responseId)

      return True

   def sendResponse(self, responseId, values=None):
      """Sends a response back to the parent process."""
      response = _createResponse(responseId, values)
      self.commandConnection.send(response)

   def sendEvent(self, eventType, objectId, args=None):
      """Sends an event to the parent process."""
      event = _createEvent(eventType, objectId, args)
      self.commandConnection.send(event)

   def _receiveAdminMessage(self):
      """
      Called by Qt when the admin pipe becomes readable.  Handles two cases:

      Admin command — a dict with 'action' key.  setRate updates the render timer;
      getRate sends the current rate back on the admin pipe.

      EOF (shutdown) — the parent closed its end of the admin pipe via _shutdown()
      or process death.  Drains any remaining commands from the command pipe,
      sending 'shutdown' responses to release any sendQuery() callers blocking in
      the parent, then quits Qt's event loop normally.
      """
      try:
         message = self.priorityConnection.recv()
      except (EOFError, OSError):
         # Admin pipe closed — initiate shutdown
         if self._commandListener is not None:
            self._commandListener.setEnabled(False)
         if self._adminListener is not None:
            self._adminListener.setEnabled(False)
         if self._adminPollTimer is not None:
            self._adminPollTimer.stop()
         self._renderTimer.stop()

         # Drain remaining commands.  Queries get a 'shutdown' response so that
         # any sendQuery() call blocking in the parent is released immediately.
         try:
            while self.commandConnection.poll():
               msg = self.commandConnection.recv()
               commands = msg if isinstance(msg, list) else [msg]
               for command in commands:
                  responseId = command.get('responseId')
                  if responseId is not None:
                     self.commandConnection.send(_createResponse(responseId, ['shutdown']))
         except (EOFError, OSError):
            pass

         self.qApplication.quit()
         return

      action = message.get('action')
      if action == 'setRate':
         self._renderRate = message.get('rate', _RENDER_RATE)
         self._renderTimer.setInterval(1000 // self._renderRate)
      elif action == 'getRate':
         self.priorityConnection.send(self._renderRate)


#######################################################################################
# Qt helper classes
#######################################################################################

class QtDisplay(QtWidgets.QMainWindow):
   """
   QMainWindow subclass used by DisplayMirror.
   Overrides closeEvent so DisplayMirror can send a 'displayClose' event to the
   parent process when the user closes the window.
   """

   def __init__(self, owner):
      super().__init__()
      self._owner = owner   # the DisplayMirror that owns this window

   def changeEvent(self, event):
      """
      Event called by Qt when the Display goes in or out of focus.
      """
      super().changeEvent(event)
      timer = self._owner._toolTipTimer
      if timer is None:
         return
      if event.type() == QtCore.QEvent.Type.WindowActivate:
         if self._owner._showCoords:
            timer.start()
      elif event.type() == QtCore.QEvent.Type.WindowDeactivate:
         timer.stop()

   def closeEvent(self, event):
      """
      Event called by Qt when the Display is closed.
      """
      self._owner.onWindowClose()
      event.accept()



#######################################################################################
# _sceneToCoord  —  scene position → float GUI coordinates
#######################################################################################

def _sceneToCoord(scenePos):
   """Converts a scene-space QPointF to the (float) GUI coordinates reported to user code.

   The view is shifted half a pixel (see DisplayMirror.__init__) so coordinate N renders at
   the CENTER of pixel N; a scene position therefore sits 0.5 below the coordinate it names.
   Adding 0.5 back inverts that.  The values are kept as floats -- GuiRenderer never coerces
   to int (the PythonMusic side decides when to round or retain sub-pixel accuracy); the
   showMouseCoordinates overlay is the one exception, and rounds at its display site.
   """
   return scenePos.x() + 0.5, scenePos.y() + 0.5


#######################################################################################
# _QtGraphicsItemEventMixin  —  event handling mixin for custom Qt item classes
#######################################################################################

class _QtGraphicsItemEventMixin:
   """
   Python mixin that adds PythonMusic event delivery to custom QGraphicsItem
   subclasses.  Inherit from this class BEFORE the Qt base class so that Python's
   MRO invokes these overrides.

   Access to GuiRenderer and mirror objectId is via self._mirror, which is set on
   every qObject by _DrawableMirror.qObject.setter immediately after construction.

   All handlers call event.ignore() so Qt continues cascading the event to items
   lower in the z-order.  QtView delivers Display-level events after super() returns,
   ensuring the Display always fires last regardless of item accept/ignore.
   """

   _CLICK_THRESHOLD = 5   # max pixel movement for press+release to count as a click

   # ── Helpers ────────────────────────────────────────────────────────────────

   def _qtview(self):
      """Returns the owning QtView, or None if the scene is not yet set."""
      scene = self.scene()
      if scene is None:
         return None
      views = scene.views()
      return views[0] if views else None

   def _send(self, eventType, args):
      """Sends an event to this item's mirror if (objectId, eventType) is registered."""
      mirror = self._mirror
      if (mirror.objectId, eventType) in mirror.guiRenderer._registeredEvents:
         mirror.guiRenderer.sendEvent(eventType, mirror.objectId, args)

   # ── Mouse ──────────────────────────────────────────────────────────────────

   def mousePressEvent(self, event):
      pos  = event.scenePos()
      args = list(_sceneToCoord(pos))
      self._send('mouseDown', args)
      # register this item for release and drag delivery during subsequent mouse events
      view = self._qtview()
      if view is not None:
         view._pressedItems.append(self._mirror.objectId)   # track for manual release delivery (see QtView.mouseReleaseEvent)
         if (self._mirror.objectId, 'mouseDrag') in self._mirror.guiRenderer._registeredEvents:
            view._draggingItems.append(self._mirror.objectId)
      event.ignore()   # allow cascade to items below

   def mouseReleaseEvent(self, event):
      pos  = event.scenePos()
      x, y = _sceneToCoord(pos)
      self._send('mouseUp', [x, y])
      # click: only if movement since press was under threshold
      view = self._qtview()
      if view is not None and view._pressPos is not None:
         dx = abs(pos.x() - view._pressPos.x())
         dy = abs(pos.y() - view._pressPos.y())
         if dx <= self._CLICK_THRESHOLD and dy <= self._CLICK_THRESHOLD:
            self._send('mouseClick', [x, y])
      event.ignore()

   # ── Hover ──────────────────────────────────────────────────────────────────

   def hoverEnterEvent(self, event):
      pos = event.scenePos()
      self._send('mouseEnter', list(_sceneToCoord(pos)))
      event.ignore()

   def hoverLeaveEvent(self, event):
      pos = event.scenePos()
      self._send('mouseExit', list(_sceneToCoord(pos)))
      event.ignore()

   def hoverMoveEvent(self, event):
      pos = event.scenePos()
      self._send('mouseMove', list(_sceneToCoord(pos)))
      event.ignore()

   # ── Keyboard ───────────────────────────────────────────────────────────────

   def keyPressEvent(self, event):
      if not event.isAutoRepeat():
         key  = event.key()
         char = event.text() if event.text() else ""
         self._send('keyDown', [key])
         if char:
            self._send('keyType', [char])
      event.ignore()   # propagate to view for Display delivery

   def keyReleaseEvent(self, event):
      if not event.isAutoRepeat():
         self._send('keyUp', [event.key()])
      event.ignore()


#######################################################################################
# Custom QGraphicsItem subclasses  —  one per shape type
#######################################################################################

class _QRectItem(_QtGraphicsItemEventMixin, QtWidgets.QGraphicsRectItem):
   pass

class _QEllipseItem(_QtGraphicsItemEventMixin, QtWidgets.QGraphicsEllipseItem):
   pass

class _QPathItem(_QtGraphicsItemEventMixin, QtWidgets.QGraphicsPathItem):
   pass

class _QLineItem(_QtGraphicsItemEventMixin, QtWidgets.QGraphicsLineItem):
   pass

class _QPolygonItem(_QtGraphicsItemEventMixin, QtWidgets.QGraphicsPolygonItem):
   pass

class _QPixmapItem(_QtGraphicsItemEventMixin, QtWidgets.QGraphicsPixmapItem):
   pass

class _QGroupItem(_QtGraphicsItemEventMixin, QtWidgets.QGraphicsItemGroup):
   pass


#######################################################################################
# QtView  —  QGraphicsView subclass for Display-level event delivery
#######################################################################################

class QtView(QtWidgets.QGraphicsView):
   """
   QGraphicsView subclass used by DisplayMirror.

   Calls super() first so Qt routes events to items in z-order (mixin handles
   item-level delivery with event.ignore() for cascade).  Display-level events
   are delivered afterwards, ensuring the Display always fires last regardless of
   whether any item accepted the event.

   _pressPos  — scene-coordinate QPointF at last press; shared with item release
                handlers for click detection.
   _draggingItems — list of objectIds registered for mouseDrag, populated during
                    press so drag events can be delivered during move.
   """

   def __init__(self, scene, displayMirror):
      super().__init__(scene)
      self._display       = displayMirror
      self._pressPos      = None   # QPointF scene pos at last press
      self._draggingItems = []     # objectIds wanting drag events
      self._pressedItems  = []     # objectIds of items that received the last mousePressEvent

   # ── Helpers ────────────────────────────────────────────────────────────────

   def _sendDisplay(self, eventType, args):
      """Sends an event to the Display if (displayId, eventType) is registered."""
      display = self._display
      if (display.objectId, eventType) in display.guiRenderer._registeredEvents:
         display.guiRenderer.sendEvent(eventType, display.objectId, args)

   def _sceneXY(self, event):
      """Maps a QMouseEvent's viewport position to integer scene coordinates."""
      vpos = self.viewport().mapFromGlobal(event.globalPosition().toPoint())
      pos  = self.mapToScene(vpos)
      return _sceneToCoord(pos)

   # ── Mouse ──────────────────────────────────────────────────────────────────

   def mousePressEvent(self, event):
      self._pressPos      = self.mapToScene(event.position().toPoint())
      self._draggingItems = []
      super().mousePressEvent(event)
      x, y = self._sceneXY(event)
      self._sendDisplay('mouseDown', [x, y])

   def mouseReleaseEvent(self, event):
      x, y = self._sceneXY(event)

      # Items call event.ignore() in mousePressEvent to allow cascade, so Qt never
      # sets a mouse grabber and mouseReleaseEvent is never routed to items normally.
      # Manually deliver mouseUp and mouseClick using the objectIds tracked at press time,
      # mirroring the _draggingItems pattern used for mouseDrag.
      registered = self._display.guiRenderer._registeredEvents
      pos        = self.mapToScene(event.position().toPoint())
      is_click   = (self._pressPos is not None
                    and abs(pos.x() - self._pressPos.x()) <= _QtGraphicsItemEventMixin._CLICK_THRESHOLD
                    and abs(pos.y() - self._pressPos.y()) <= _QtGraphicsItemEventMixin._CLICK_THRESHOLD)
      for objectId in self._pressedItems:
         if (objectId, 'mouseUp') in registered:
            self._display.guiRenderer.sendEvent('mouseUp', objectId, [x, y])
         if is_click and (objectId, 'mouseClick') in registered:
            self._display.guiRenderer.sendEvent('mouseClick', objectId, [x, y])

      self._sendDisplay('mouseUp', [x, y])
      if is_click:
         self._sendDisplay('mouseClick', [x, y])
      self._pressPos      = None
      self._draggingItems = []
      self._pressedItems  = []

   def mouseMoveEvent(self, event):
      x, y = self._sceneXY(event)
      super().mouseMoveEvent(event)    # → hover events on items (button up)
      
      # decide whether to show tooltip, and what to show
      if self._display.toolTipQLabel is not None:
         vpos = self.viewport().mapFromGlobal(event.globalPosition().toPoint())
         if self._display._showCoords:
            self._display._placeOverlayLabel(vpos.x(), vpos.y(), f'({int(x)}, {int(y)})')
         else:
            self._display._updateNonCoordLabel(vpos)

      # is this a mouse move or mouse drag?
      if event.buttons() == QtCore.Qt.MouseButton.NoButton:
         # move: just deliver to display
         self._sendDisplay('mouseMove', [x, y])
      else:
         # drag: deliver to items that were under the cursor at press time
         registered = self._display.guiRenderer._registeredEvents
         for objectId in self._draggingItems:
            if (objectId, 'mouseDrag') in registered:
               self._display.guiRenderer.sendEvent('mouseDrag', objectId, [x, y])
         # then deliver to display
         self._sendDisplay('mouseDrag', [x, y])

   def enterEvent(self, event):
      super().enterEvent(event)
      self._sendDisplay('mouseEnter', [0, 0])
      self._display._mouseOnDisplay = True
      if not self._display._showCoords:
         self._display._createOverlayLabel()
         vpos = self.viewport().mapFromGlobal(QtGui.QCursor.pos())
         self._display._updateNonCoordLabel(vpos)

   def leaveEvent(self, event):
      super().leaveEvent(event)
      self._sendDisplay('mouseExit', [0, 0])
      self._display._mouseOnDisplay = False
      if not self._display._showCoords and self._display.toolTipQLabel is not None:
         self._display.toolTipQLabel.hide()

   # ── Keyboard ───────────────────────────────────────────────────────────────

   def keyPressEvent(self, event):
      if not event.isAutoRepeat():
         key  = event.key()
         char = event.text() if event.text() else ""
         super().keyPressEvent(event)   # → focused item via mixin
         self._sendDisplay('keyDown', [key])
         if char:
            self._sendDisplay('keyType', [char])
      else:
         super().keyPressEvent(event)

   def keyReleaseEvent(self, event):
      if not event.isAutoRepeat():
         super().keyReleaseEvent(event)  # → focused item via mixin
         self._sendDisplay('keyUp', [event.key()])
      else:
         super().keyReleaseEvent(event)


#######################################################################################
# _detachItem  —  reparenting helper shared by DisplayMirror and GroupMirror
#######################################################################################

def _detachItem(item):
   """Removes a mirror's QGraphicsItem from its current parent and scene, if any, so
   it can be cleanly re-attached to a different Display or Group."""
   q      = item.qObject
   parent = q.parentItem()
   if isinstance(parent, QtWidgets.QGraphicsItemGroup):
      parent.removeFromGroup(q)   # proper inverse of addToGroup; keeps the group's members in sync
   elif parent is not None:
      q.setParentItem(None)
   if q.scene() is not None:
      q.scene().removeItem(q)


#######################################################################################
# DisplayMirror  —  mirror of gui.py's Display
#######################################################################################

class DisplayMirror:
   """
   Mirror of gui.py's Display class.  Owns all Qt objects for one display window.

   Created by GuiRenderer when it receives a 'create' command with type='Display'.
   All subsequent operations arrive as commands routed through handleCommand().

   add / addOrder / remove
   -----------------------
   Items on a Display are tracked in _itemList (front = top z-order).  Qt z-order
   is maintained as a float qZValue on each mirror object so that insertions only
   require averaging two neighbours rather than renumbering the entire list.
   """

   def __init__(self, objectId, args, guiRenderer):
      """
      Creates the Qt window, scene, view, and OpenGL viewport for one Display.
      """
      self.objectId        = objectId
      self.guiRenderer     = guiRenderer
      self._itemList       = []
      self._toolTipText    = None   # this display's tool tip text (None = disabled)
      self._showCoords     = False  # should our tooltip show mouse coordinates?
      self._mouseOnDisplay = False  # is the mouse currently over the display?
      self.toolTipQLabel   = None   # shared QLabel for tooltips
      self._overlayOffset  = 14     # px offset from cursor tip to overlay label
      self._toolTipTimer   = None   # QTimer for off-display coordinate polling

      title  = args.get('title',  '')
      width  = args.get('width',  600)
      height = args.get('height', 400)
      x      = args.get('x',     0)
      y      = args.get('y',     50)
      color  = args.get('color', [255, 255, 255, 255])

      self._window = QtDisplay(self)
      self._window.setWindowTitle(title)
      self._window.setGeometry(x, y, width, height)
      self._window.setFixedSize(width, height)
      contextPolicy = QtCore.Qt.ContextMenuPolicy.CustomContextMenu
      self._window.setContextMenuPolicy(contextPolicy)
      self._window.show()
      self._window.raise_()
      self._window.activateWindow()

      # Qt 6's default software rasterizer (raster engine) is sufficient for
      # 2D educational graphics and works consistently across all platforms.
      # QOpenGLWidget was previously used here for hardware acceleration, but
      # on macOS its OpenGL→Metal bridge conflicted with native AppKit dialogs
      # (NSColorPicker, etc.) that also use Metal, causing the GPU shader
      # compiler to abort (SIGABRT in AGXMetal).  Removing it eliminates that
      # crash, simplifies the code, and gives identical behavior on every OS.
      # The OS window manager still handles GPU compositing of the final window.
      self._scene   = QtWidgets.QGraphicsScene(0, 0, width, height)
      self._view    = QtView(self._scene, self)
      self._window.setCentralWidget(self._view)

      noIndex       = QtWidgets.QGraphicsScene.ItemIndexMethod.NoIndex
      minimalUpdate = QtWidgets.QGraphicsView.ViewportUpdateMode.MinimalViewportUpdate
      hoverTracking = QtCore.Qt.WidgetAttribute.WA_Hover
      mouseTracking = QtCore.Qt.WidgetAttribute.WA_MouseTracking
      scrollOff     = QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
      antiAlias     = QtGui.QPainter.RenderHint.Antialiasing
      smoothPixmap  = QtGui.QPainter.RenderHint.SmoothPixmapTransform
      textAntiAlias = QtGui.QPainter.RenderHint.TextAntialiasing

      self._scene.setItemIndexMethod(noIndex)
      self._view.setViewportUpdateMode(minimalUpdate)
      self._view.setAttribute(hoverTracking,  True)
      self._view.setAttribute(mouseTracking,  True)
      self._view.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
      self._view.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop)
      self._view.setHorizontalScrollBarPolicy(scrollOff)
      self._view.setVerticalScrollBarPolicy(scrollOff)
      self._view.setRenderHint(antiAlias,     True)
      self._view.setRenderHint(smoothPixmap,  True)
      self._view.setRenderHint(textAntiAlias, True)

      # Integer GUI coordinates name pixels, but in Qt scene space an integer N is the
      # boundary between pixels N-1 and N, not the center of a pixel.  Shift the view by
      # half a pixel so coordinate N maps to the CENTER of pixel N.  Without this, a shape
      # at coordinate 0 has half its antialiased stroke clipped by the scene's top/left
      # edge, while the same shape near the far edge (e.g. width-1) renders fully, so two
      # supposedly symmetric shapes clip asymmetrically.  This rides on the view transform
      # (not the scroll offset), so it also holds while a scrollable Display is scrolled,
      # and mapToScene compensates automatically so mouse coordinates stay consistent.
      self._view.translate(0.5, 0.5)

      r, g, b, a = color
      qColor     = QtGui.QColor(r, g, b, a)
      brush      = QtGui.QBrush(qColor)
      self._scene.setBackgroundBrush(brush)
      self._view.setBackgroundBrush(brush)

      # Persistent draw layer — a transparent pixmap that one-time draw calls paint onto.
      # Sits at z = -1e9, permanently below all instantiated objects (which start at z=1.0
      # and decrease).  Never added to _itemList, so it is invisible to hit-testing,
      # removeAll, and z-order management.
      # Sized at the screen's device pixel ratio so painted shapes render at native
      # resolution on HiDPI displays — otherwise the view bilinear-upscales a 1x pixmap,
      # producing blurry low-res shapes vs. crisp QGraphicsItems added via add().
      self._drawPixmap = self._makeDrawPixmap(width, height)
      self._drawLayer  = QtWidgets.QGraphicsPixmapItem(self._drawPixmap)
      self._drawLayer.setZValue(-1e9)
      self._scene.addItem(self._drawLayer)

      self._commandHandlers = {
         'show':                 self._show,
         'hide':                 self._hide,
         'close':                self._close,
         'addOrder':             self._addOrder,
         'remove':               self._remove,
         'removeAll':            self._removeAll,
         'move':                 self._move,
         'getOrder':             self._getOrder,
         'setOrder':             self._setOrder,
         'getColor':             self._getColor,
         'setColor':             self._setColor,
         'getTitle':             self._getTitle,
         'setTitle':             self._setTitle,
         'getWidth':             self._getWidth,
         'getHeight':            self._getHeight,
         'getSize':              self._getSize,
         'setSize':              self._setSize,
         'setScrollable':        self._setScrollable,
         'getPosition':          self._getPosition,
         'setPosition':          self._setPosition,
         'setToolTipText':       self._setToolTipText,
         'showMouseCoordinates': self._showMouseCoordinates,
         'hideMouseCoordinates': self._hideMouseCoordinates,
         'addMenu':              self._addMenu,
         'addPopupMenu':         self._addPopupMenu,
         'write':                self._write,
         'draw':                 self._draw,
         'clearDrawing':         self._clearDrawing,
      }

      self._drawHandlers = {
         'rectangle': self._drawRectangle,
         'oval':      self._drawOval,
         'circle':    self._drawOval,
         'point':     self._drawOval,
         'arc':       self._drawArc,
         'line':      self._drawLine,
         'polyline':  self._drawPolyline,
         'polygon':   self._drawPolygon,
         'icon':      self._drawIcon,
         'label':     self._drawLabel,
      }

      self._popupMenu = None
      self._window.customContextMenuRequested.connect(self._onContextMenuRequested)


   def handleCommand(self, action, args, responseId):
      handler = self._commandHandlers.get(action)
      if handler is not None:
         handler(args, responseId)

   # ── Window visibility ──────────────────────────────────────────────────────

   def _show(self, args, responseId):
      self._window.show()

   def _hide(self, args, responseId):
      self._window.hide()

   def _close(self, args, responseId):
      self._window.close()

   # ── Item management ────────────────────────────────────────────────────────

   def _addOrder(self, args, responseId):
      """Adds an item at the specified z-order position."""
      itemId = args.get('itemId')
      order  = args.get('order', 0)

      # find the item's mirror object
      item = self.guiRenderer._objectRegistry.get(itemId)

      # if we found a valid item...
      if item is not None:

         # add to PythonMusic-format item list
         self._itemList.insert(order, item)

         # convert PythonMusic z-order to Qt z-value
         # (PythonMusic is front-to-back, Qt is back-to-front)
         if order == 0:
            # adding to top (most common)
            qZValue = 1.0
            if len(self._itemList) > 1:
               neighbor = self._itemList[1]        # find former topmost item's z-value
               qZValue  = neighbor.qZValue + 1.0  # and go one higher

         elif order >= len(self._itemList) - 1:
            # adding to back
            qZValue = 0.0
            if len(self._itemList) > 1:
               neighbor = self._itemList[-2]       # find former bottommost item's z-value
               qZValue  = neighbor.qZValue - 1.0  # and go one lower

         else:
            # adding somewhere in the middle
            frontNeighbor = self._itemList[order - 1]  # find surrounding neighbor's z-values
            backNeighbor  = self._itemList[order + 1]  # and go between them
            qZValue       = (frontNeighbor.qZValue + backNeighbor.qZValue) / 2.0

         item.qZValue = qZValue  # store found z-value


         if isinstance(item, _ControlMirror):
            item.qObject.setParent(self._window)  # attach QWidget to window
            item.qObject.show()
            item._applyTransform()                 # widgets reset position on reparent, so place it now
         else:
            _detachItem(item)                      # detach from any previous parent/scene
            item.qObject.setZValue(qZValue)
            self._scene.addItem(item.qObject)      # attach as a top-level scene item

         # the item's position/rotation/scale arrive separately via setTransform,
         # so there is nothing to position here.

   def _remove(self, args, responseId):
      itemId = args.get('itemId')
      item = self.guiRenderer._objectRegistry.get(itemId)
      if item is not None and item in self._itemList:
         self._itemList.remove(item)
         if isinstance(item, _ControlMirror):
            item.qObject.setParent(None)     # detach QWidget from window
            item.qObject.hide()
         else:
            _detachItem(item)

   def _removeAll(self, args, responseId):
      self._view.setUpdatesEnabled(False)
      for item in list(self._itemList):
         if isinstance(item, _ControlMirror):
            item.qObject.setParent(None)
            item.qObject.hide()
         else:
            self._scene.removeItem(item.qObject)
      self._itemList.clear()
      self._view.setUpdatesEnabled(True)
      self._view.viewport().update()

   def _move(self, args, responseId):
      itemId = args.get('itemId')
      x      = args.get('x')
      y      = args.get('y')
      item = self.guiRenderer._objectRegistry.get(itemId)
      if item is not None and item in self._itemList:
         item._setPosition({'x': x, 'y': y}, responseId=None)

   def _getOrder(self, args, responseId):
      itemId = args.get('itemId')
      order  = None
      for i, item in enumerate(self._itemList):
         if item.objectId == itemId:
            order = i
            break
      self.guiRenderer.sendResponse(responseId, [order])

   def _setOrder(self, args, responseId):
      itemId       = args.get('itemId')
      order        = args.get('order', 0)
      addOrderArgs = {'itemId': itemId, 'order': order, 'x': None, 'y': None}
      self._addOrder(addOrderArgs, responseId=None)

   # ── Color ──────────────────────────────────────────────────────────────────

   def _getColor(self, args, responseId):
      qColor = self._scene.backgroundBrush().color()
      r      = qColor.red()
      g      = qColor.green()
      b      = qColor.blue()
      a      = qColor.alpha()
      self.guiRenderer.sendResponse(responseId, [r, g, b, a])

   def _setColor(self, args, responseId):
      color      = args.get('color', [255, 255, 255, 255])
      r, g, b, a = color
      qColor     = QtGui.QColor(r, g, b, a)
      brush      = QtGui.QBrush(qColor)
      self._scene.setBackgroundBrush(brush)
      self._view.setBackgroundBrush(brush)

   # ── Title ──────────────────────────────────────────────────────────────────

   def _getTitle(self, args, responseId):
      title = self._window.windowTitle()
      self.guiRenderer.sendResponse(responseId, [title])

   def _setTitle(self, args, responseId):
      title = args.get('title', '')
      self._window.setWindowTitle(title)

   # ── Size ───────────────────────────────────────────────────────────────────

   def _getWidth(self, args, responseId):
      self.guiRenderer.sendResponse(responseId, [int(self._scene.width())])

   def _getHeight(self, args, responseId):
      self.guiRenderer.sendResponse(responseId, [int(self._scene.height())])

   def _getSize(self, args, responseId):
      width  = int(self._scene.width())
      height = int(self._scene.height())
      self.guiRenderer.sendResponse(responseId, [width, height])

   def _setSize(self, args, responseId):
      width  = args.get('width',  600)
      height = args.get('height', 400)
      if width > 0 and height > 0:
         pos = self._window.pos()
         self._scene.setSceneRect(0, 0, width, height)
         self._window.setFixedSize(width, height)
         self._window.move(pos)

         # Recreate the draw layer at the new dimensions.  The old drawing is cleared
         # because scaling painted geometry would distort it.
         self._drawPixmap = self._makeDrawPixmap(width, height)
         self.guiRenderer._dirtyDisplays.add(self)

   def _setScrollable(self, args, responseId):
      # Window keeps its current pixel size as the viewport; the scene grows
      # to (sceneWidth, sceneHeight) and the QGraphicsView shows scrollbars
      # when the viewport is smaller.  Hit-testing, hover, tooltips, and
      # mouse-coordinate overlays do not account for scroll offset.
      sceneWidth  = args.get('sceneWidth',  int(self._scene.width()))
      sceneHeight = args.get('sceneHeight', int(self._scene.height()))

      self._window.setMinimumSize(200, 150)
      self._window.setMaximumSize(16777215, 16777215)   # Qt's QWIDGETSIZE_MAX
      asNeeded = QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded
      self._view.setHorizontalScrollBarPolicy(asNeeded)
      self._view.setVerticalScrollBarPolicy(asNeeded)
      self._scene.setSceneRect(0, 0, sceneWidth, sceneHeight)

   # ── Position ───────────────────────────────────────────────────────────────

   def _getPosition(self, args, responseId):
      x = int(self._window.x())
      y = int(self._window.y())
      self.guiRenderer.sendResponse(responseId, [x, y])

   def _setPosition(self, args, responseId):
      x      = int(args.get('x', 0))
      y      = int(args.get('y', 0))
      width  = int(self._scene.width())
      height = int(self._scene.height())
      self._window.setGeometry(x, y, width, height)

   # ── Tooltip ────────────────────────────────────────────────────────────────

   def _setToolTipText(self, args, responseId):
      text              = args.get('text')
      self._toolTipText = text
      self._view.setToolTip(None)   # always disabled; overlay label manages display
      if not self._showCoords and self.toolTipQLabel is not None:
         if text and self._mouseOnDisplay:
            self.toolTipQLabel.setText(text)
            self.toolTipQLabel.adjustSize()
            self.toolTipQLabel.show()
            self.toolTipQLabel.raise_()
         else:
            self.toolTipQLabel.hide()

   def _createOverlayLabel(self):
      """Creates and styles the shared overlay label as a viewport child, if not already created."""
      if self.toolTipQLabel is not None:
         return
      label = QtWidgets.QLabel(self._view.viewport())
      tt_pal = QtWidgets.QToolTip.palette()
      bg = tt_pal.color(QtGui.QPalette.ColorRole.ToolTipBase).name()
      fg = tt_pal.color(QtGui.QPalette.ColorRole.ToolTipText).name()
      label.setStyleSheet(
         f'QLabel {{ background-color: {bg}; color: {fg};'
         f' border: 1px solid {fg}; padding: 2px 4px; }}'
      )
      label.setFont(QtWidgets.QToolTip.font())
      label.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents)
      label.hide()
      self.toolTipQLabel = label

   def _showMouseCoordinates(self, args, responseId):
      self._showCoords = True
      self._view.setToolTip(None)
      self._createOverlayLabel()
      self.toolTipQLabel.show()
      self.toolTipQLabel.raise_()
      if self._toolTipTimer is None:
         timer = QtCore.QTimer()
         timer.setInterval(50)
         timer.timeout.connect(self._updateCoordLabel)
         self._toolTipTimer = timer
      self._toolTipTimer.start()

   def _updateCoordLabel(self):
      """Polls cursor position for off-display coordinate tracking."""
      vp   = self._view.viewport()
      vpos = vp.mapFromGlobal(QtGui.QCursor.pos())
      cvx  = max(0, min(vpos.x(), vp.width()  - 1))
      cvy  = max(0, min(vpos.y(), vp.height() - 1))
      spos = self._view.mapToScene(QtCore.QPoint(cvx, cvy))
      sx, sy = _sceneToCoord(spos)
      self._placeOverlayLabel(cvx, cvy, f'({int(sx)}, {int(sy)})')

   def _tooltipTextAt(self, vpos):
      """
      Returns the tooltip text that should be shown for the item under vpos
      (viewport-relative QPoint), or None if there is nothing to show.
      Priority: control widget > topmost scene item > display tooltip.
      """
      # 1. Control widget under cursor
      globalPos = self._view.viewport().mapToGlobal(vpos)
      widget = QtWidgets.QApplication.widgetAt(globalPos)
      if widget is not None:
         for item in self._itemList:
            if isinstance(item, _ControlMirror) and item._toolTipText:
               w = widget
               while w is not None:
                  if w is item.qObject:
                     return item._toolTipText
                  w = w.parentWidget()

      # 2. Topmost scene item at cursor position
      scenePos = self._view.mapToScene(vpos)
      for qitem in self._scene.items(scenePos):
         mirror = getattr(qitem, '_mirror', None)
         if mirror is not None and mirror._toolTipText:
            return mirror._toolTipText

      # 3. Display tooltip
      return self._toolTipText

   def _updateNonCoordLabel(self, vpos):
      """Shows the correct tooltip (item or display) at vpos, or hides if none."""
      if self.toolTipQLabel is None:
         return
      text = self._tooltipTextAt(vpos)
      if text:
         self._placeOverlayLabel(vpos.x(), vpos.y(), text)
         self.toolTipQLabel.show()
      else:
         self.toolTipQLabel.hide()

   def _placeOverlayLabel(self, vx, vy, text):
      """Sets the overlay label text and positions it near (vx, vy) in viewport coords."""
      label  = self.toolTipQLabel
      offset = self._overlayOffset
      label.setText(text)
      label.adjustSize()
      vp = self._view.viewport()
      lx = vx + offset
      ly = vy + offset
      if lx + label.width()  > vp.width()  - 2:
         lx = vx - label.width()  - offset
      if ly + label.height() > vp.height() - 2:
         ly = vy - label.height() - offset
      label.move(max(0, lx), max(0, ly))
      label.raise_()

   def _hideMouseCoordinates(self, args, responseId):
      self._showCoords = False
      if self._toolTipTimer is not None:
         self._toolTipTimer.stop()
      if self.toolTipQLabel is not None and self._mouseOnDisplay:
         vpos = self._view.viewport().mapFromGlobal(QtGui.QCursor.pos())
         self._updateNonCoordLabel(vpos)
      elif self.toolTipQLabel is not None:
         self.toolTipQLabel.hide()

   # ── Menu ───────────────────────────────────────────────────────────────────

   def _addMenu(self, args, responseId):
      menuId = args.get('menuId')
      menu   = self.guiRenderer._objectRegistry.get(menuId)
      if menu is not None:
         self._window.menuBar().addMenu(menu._qMenu)

   def _addPopupMenu(self, args, responseId):
      menuId = args.get('menuId')
      menu   = self.guiRenderer._objectRegistry.get(menuId)
      if menu is not None:
         self._popupMenu = menu._qMenu

   def _onContextMenuRequested(self, pos):
      if self._popupMenu is not None:
         globalPos = self._window.mapToGlobal(pos)
         self._popupMenu.exec(globalPos)

   # ── Draw layer ─────────────────────────────────────────────────────────────

   def _draw(self, args, responseId):
      """Dispatches a one-time draw command to the appropriate shape painter."""
      shape   = args.get('shape')
      handler = self._drawHandlers.get(shape)
      if handler is not None:
         handler(args)

   def _clearDrawing(self, args, responseId):
      """Clears all one-time drawn content from the draw layer."""
      self._drawPixmap.fill(QtCore.Qt.GlobalColor.transparent)
      self.guiRenderer._dirtyDisplays.add(self)

   def _makeDrawPixmap(self, width, height):
      """
      Creates a transparent QPixmap sized for the screen's device pixel ratio.

      On HiDPI displays (e.g. macOS Retina, dpr=2) the underlying buffer is dpr× the
      logical size in each axis, with the pixmap's dpr set so QGraphicsPixmapItem
      displays it at logical size and QPainter operates in logical coordinates.
      Result: drawn shapes render at native resolution instead of being
      bilinear-upscaled from a 1× buffer.
      """
      dpr    = self._window.devicePixelRatioF()
      pixmap = QtGui.QPixmap(int(width * dpr), int(height * dpr))
      pixmap.setDevicePixelRatio(dpr)
      pixmap.fill(QtCore.Qt.GlobalColor.transparent)
      return pixmap

   def _openDrawPainter(self, visibility=100):
      """Opens an antialiased QPainter on the draw pixmap and returns it.  The painter's
      opacity is set from visibility (0 = invisible, 100 = fully visible) so every shape
      it paints is drawn at that opacity."""
      painter = QtGui.QPainter(self._drawPixmap)
      painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
      painter.setRenderHint(QtGui.QPainter.RenderHint.SmoothPixmapTransform)
      painter.setOpacity(max(0, min(100, visibility)) / 100.0)
      return painter

   def _closeDrawPainter(self, painter):
      """Ends the painter and marks this display's draw layer dirty for deferred flush."""
      painter.end()
      self.guiRenderer._dirtyDisplays.add(self)

   def _makeDrawPen(self, color, thickness):
      """Returns a QPen for the given [r,g,b,a] color and line thickness."""
      r, g, b, a = color
      pen = QtGui.QPen(QtGui.QColor(r, g, b, a))
      pen.setWidth(thickness)
      return pen

   def _makeDrawBrush(self, color, fill):
      """Returns a filled QBrush if fill is True, otherwise NoBrush."""
      if fill:
         r, g, b, a = color
         return QtGui.QBrush(QtGui.QColor(r, g, b, a))
      return QtGui.QBrush(QtCore.Qt.BrushStyle.NoBrush)

   def _drawOval(self, args):
      """
      Paints an ellipse (or circle) onto the draw layer.
      Used by both 'oval' and 'circle' draw commands.

      Args:
        x, y          — top-left corner of the bounding box
        width, height — bounding box dimensions
        color         — [r, g, b, a]
        fill          — bool
        thickness     — int (line width)
        rotation      — degrees (CCW visual)
      """
      x         = args.get('x',         0)
      y         = args.get('y',         0)
      width     = args.get('width',     10)
      height    = args.get('height',    10)
      color      = args.get('color',      [0, 0, 0, 255])
      fill       = args.get('fill',       False)
      thickness  = args.get('thickness',  1)
      rotation   = args.get('rotation',   0)
      visibility = args.get('visibility', 100)

      painter = self._openDrawPainter(visibility)
      painter.setPen(self._makeDrawPen(color, thickness))
      painter.setBrush(self._makeDrawBrush(color, fill))

      if rotation != 0:
         cx = x + width  / 2
         cy = y + height / 2
         painter.translate(cx, cy)
         painter.rotate(-rotation)   # Qt rotates CW; CP rotation is CCW visual
         painter.drawEllipse(QtCore.QRectF(-width / 2, -height / 2, width, height))
      else:
         painter.drawEllipse(QtCore.QRectF(x, y, width, height))

      self._closeDrawPainter(painter)

   def _drawRectangle(self, args):
      """
      Paints a rectangle onto the draw layer.

      Args:
        x, y          — top-left corner of the bounding box
        width, height — bounding box dimensions
        color         — [r, g, b, a]
        fill          — bool
        thickness     — int (line width)
        rotation      — degrees (CCW visual)
      """
      x         = args.get('x',         0)
      y         = args.get('y',         0)
      width     = args.get('width',     10)
      height    = args.get('height',    10)
      color      = args.get('color',      [0, 0, 0, 255])
      fill       = args.get('fill',       False)
      thickness  = args.get('thickness',  1)
      rotation   = args.get('rotation',   0)
      visibility = args.get('visibility', 100)

      painter = self._openDrawPainter(visibility)
      painter.setPen(self._makeDrawPen(color, thickness))
      painter.setBrush(self._makeDrawBrush(color, fill))

      if rotation != 0:
         cx = x + width  / 2
         cy = y + height / 2
         painter.translate(cx, cy)
         painter.rotate(-rotation)
         painter.drawRect(QtCore.QRectF(-width / 2, -height / 2, width, height))
      else:
         painter.drawRect(QtCore.QRectF(x, y, width, height))

      self._closeDrawPainter(painter)

   def _drawArc(self, args):
      """
      Paints an arc (open, pie, or chord) onto the draw layer.
      Uses the same QPainterPath construction as ArcMirror.

      Args:
        x, y          — top-left corner of the bounding box
        width, height — bounding box dimensions
        startAngle    — degrees
        endAngle      — degrees
        style         — 0 (PIE), 1 (OPEN), 2 (CHORD)
        color         — [r, g, b, a]
        fill          — bool
        thickness     — int (line width)
        rotation      — degrees (CCW visual)
      """
      x          = args.get('x',          0)
      y          = args.get('y',          0)
      width      = args.get('width',      100)
      height     = args.get('height',     100)
      startAngle = args.get('startAngle', 180)
      endAngle   = args.get('endAngle',   360)
      style      = args.get('style',      _OPEN)
      color      = args.get('color',      [0, 0, 0, 255])
      fill       = args.get('fill',       False)
      thickness  = args.get('thickness',  1)
      rotation   = args.get('rotation',   0)
      visibility = args.get('visibility', 100)

      arcWidth = -(endAngle - startAngle)   # Qt sweeps CW for positive span

      path = QtGui.QPainterPath()
      path.arcMoveTo(0, 0, width, height, startAngle)
      path.arcTo(0, 0, width, height, startAngle, arcWidth)
      if style == _PIE:
         path.lineTo(width / 2, height / 2)
         path.closeSubpath()
      elif style == _CHORD:
         path.closeSubpath()

      painter = self._openDrawPainter(visibility)
      painter.setPen(self._makeDrawPen(color, thickness))
      painter.setBrush(self._makeDrawBrush(color, fill))

      if rotation != 0:
         cx = x + width  / 2
         cy = y + height / 2
         painter.translate(cx, cy)
         painter.rotate(-rotation)
         painter.translate(-width / 2, -height / 2)
      else:
         painter.translate(x, y)

      painter.drawPath(path)
      self._closeDrawPainter(painter)

   def _drawLine(self, args):
      """
      Paints a line segment onto the draw layer.
      Rotation is applied around the line's midpoint.

      Args:
        x1, y1, x2, y2 — endpoint coordinates (scene space)
        color           — [r, g, b, a]
        thickness       — int (line width)
        rotation        — degrees (CCW visual)
      """
      x1        = args.get('x1',        0)
      y1        = args.get('y1',        0)
      x2         = args.get('x2',         100)
      y2         = args.get('y2',         100)
      color      = args.get('color',      [0, 0, 0, 255])
      thickness  = args.get('thickness',  1)
      rotation   = args.get('rotation',   0)
      visibility = args.get('visibility', 100)

      painter = self._openDrawPainter(visibility)
      painter.setPen(self._makeDrawPen(color, thickness))

      if rotation != 0:
         mx = (x1 + x2) / 2
         my = (y1 + y2) / 2
         painter.translate(mx, my)
         painter.rotate(-rotation)
         painter.translate(-mx, -my)

      painter.drawLine(QtCore.QPointF(x1, y1), QtCore.QPointF(x2, y2))
      self._closeDrawPainter(painter)

   def _drawPolyline(self, args):
      """
      Paints an open polyline onto the draw layer.
      Rotation is applied around the bounding box center.

      Args:
        xPoints   — list of x coordinates (scene space)
        yPoints   — list of y coordinates (scene space)
        color     — [r, g, b, a]
        thickness — int (line width)
        rotation  — degrees (CCW visual)
      """
      xPoints    = args.get('xPoints',    [0, 100])
      yPoints    = args.get('yPoints',    [0, 100])
      color      = args.get('color',      [0, 0, 0, 255])
      thickness  = args.get('thickness',  1)
      rotation   = args.get('rotation',   0)
      visibility = args.get('visibility', 100)

      points  = [QtCore.QPointF(x, y) for x, y in zip(xPoints, yPoints)]
      polygon = QtGui.QPolygonF(points)

      painter = self._openDrawPainter(visibility)
      painter.setPen(self._makeDrawPen(color, thickness))
      painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)

      if rotation != 0:
         cx = (min(xPoints) + max(xPoints)) / 2
         cy = (min(yPoints) + max(yPoints)) / 2
         painter.translate(cx, cy)
         painter.rotate(-rotation)
         painter.translate(-cx, -cy)

      painter.drawPolyline(polygon)
      self._closeDrawPainter(painter)

   def _drawPolygon(self, args):
      """
      Paints a closed polygon onto the draw layer.
      Rotation is applied around the bounding box center.

      Args:
        xPoints   — list of x coordinates (scene space)
        yPoints   — list of y coordinates (scene space)
        color     — [r, g, b, a]
        fill      — bool
        thickness — int (line width)
        rotation  — degrees (CCW visual)
      """
      xPoints    = args.get('xPoints',    [0, 100, 50])
      yPoints    = args.get('yPoints',    [0,   0, 100])
      color      = args.get('color',      [0, 0, 0, 255])
      fill       = args.get('fill',       False)
      thickness  = args.get('thickness',  1)
      rotation   = args.get('rotation',   0)
      visibility = args.get('visibility', 100)

      points  = [QtCore.QPointF(x, y) for x, y in zip(xPoints, yPoints)]
      polygon = QtGui.QPolygonF(points)

      painter = self._openDrawPainter(visibility)
      painter.setPen(self._makeDrawPen(color, thickness))
      painter.setBrush(self._makeDrawBrush(color, fill))

      if rotation != 0:
         cx = (min(xPoints) + max(xPoints)) / 2
         cy = (min(yPoints) + max(yPoints)) / 2
         painter.translate(cx, cy)
         painter.rotate(-rotation)
         painter.translate(-cx, -cy)

      painter.drawPolygon(polygon)
      self._closeDrawPainter(painter)

   def _drawIcon(self, args):
      """
      Paints an image file onto the draw layer.

      Args:
        filename      — path to the image file
        x, y          — top-left position in scene space
        width, height — target dimensions (None = use pixmap's native size)
        rotation      — degrees (CCW visual)
      """
      filename   = args.get('filename',   '')
      x          = args.get('x',          0)
      y          = args.get('y',          0)
      width      = args.get('width')
      height     = args.get('height')
      rotation   = args.get('rotation',   0)
      visibility = args.get('visibility', 100)

      pixmap = QtGui.QPixmap(filename)
      if pixmap.isNull():
         return

      if width is None and height is None:
         width  = pixmap.width()
         height = pixmap.height()
      elif width is None:
         width  = int(pixmap.width() * (height / pixmap.height()))
      elif height is None:
         height = int(pixmap.height() * (width / pixmap.width()))

      pixmap = pixmap.scaled(int(width), int(height),
                             QtCore.Qt.AspectRatioMode.IgnoreAspectRatio,
                             QtCore.Qt.TransformationMode.SmoothTransformation)

      painter = self._openDrawPainter(visibility)

      if rotation != 0:
         cx = x + width  / 2
         cy = y + height / 2
         painter.translate(cx, cy)
         painter.rotate(-rotation)
         painter.drawPixmap(QtCore.QPointF(-width / 2, -height / 2), pixmap)
      else:
         painter.drawPixmap(QtCore.QPointF(x, y), pixmap)

      self._closeDrawPainter(painter)

   def _drawLabel(self, args):
      """
      Paints a text string onto the draw layer.
      Text is positioned with its top-left at (x, y), matching Label's placement.

      Args:
        text  — string
        x, y  — top-left of the text in scene space
        color — [r, g, b, a]
        font  — None, or [name, [weight, italic], size]
      """
      text       = str(args.get('text',  ''))
      x          = args.get('x',          0)
      y          = args.get('y',          0)
      color      = args.get('color',      [0, 0, 0, 255])
      font       = args.get('font')
      visibility = args.get('visibility', 100)

      painter = self._openDrawPainter(visibility)

      r, g, b, a = color
      painter.setPen(QtGui.QColor(r, g, b, a))

      if font is not None:
         name, style, size = font
         weight, italic    = style
         qFont = QtGui.QFont(name, size)
         qFont.setWeight(QtGui.QFont.Weight(weight))
         qFont.setItalic(italic)
         painter.setFont(qFont)

      # QRectF positions top-left at (x, y), matching Label's setPos behavior
      painter.drawText(
         QtCore.QRectF(x, y, self._drawPixmap.width(), self._drawPixmap.height()),
         QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.TextFlag.TextSingleLine,
         text)

      self._closeDrawPainter(painter)

   # ── Write ──────────────────────────────────────────────────────────────────

   def _write(self, args, responseId):
      """
      Saves a screenshot of the display window's current contents to a file:
      background brush, painted draw layer, all added items, and Controls
      (QWidgets parented to the window).  Optional width/height args resize
      the output; omitting one preserves aspect ratio.
      Sends [success (bool), resolvedPath (str)] back to the parent process.
      """
      import os
      filename = args.get('filename', 'display.png')
      width    = args.get('width')
      height   = args.get('height')

      # End-of-tick flush hasn't happened yet; sync the draw layer now so any
      # draw* calls made earlier in this batch are included in the grab.
      if self in self.guiRenderer._dirtyDisplays:
         self._drawLayer.setPixmap(self._drawPixmap)
         self.guiRenderer._dirtyDisplays.discard(self)

      # grab() synchronously paints the window and all child widgets, so the
      # captured pixmap covers the QGraphicsView output plus every Control.
      pixmap = self._window.grab()

      if width is not None or height is not None:
         origW  = pixmap.width()
         origH  = pixmap.height()
         width  = int(origW * (height / origH)) if width  is None else int(width)
         height = int(origH * (width  / origW)) if height is None else int(height)
         pixmap = pixmap.scaled(width, height,
                                QtCore.Qt.AspectRatioMode.IgnoreAspectRatio,
                                QtCore.Qt.TransformationMode.SmoothTransformation)

      success      = pixmap.save(filename)
      resolvedPath = os.path.abspath(filename)
      self.guiRenderer.sendResponse(responseId, [success, resolvedPath])

   # ── Close event ────────────────────────────────────────────────────────────

   def onWindowClose(self):
      isRegistered = (self.objectId, 'displayClose') in self.guiRenderer._registeredEvents
      if isRegistered:
         self.guiRenderer.sendEvent('displayClose', self.objectId, {})


#######################################################################################
# _DrawableMirror  —  base mirror for all drawable items
#######################################################################################

class _DrawableMirror:
   """
   Base class for all mirror objects that can be placed on a Display.
   Provides position, size, rotation, hit-testing, visibility, and tooltip command handlers.

   Concrete classes (e.g. RectangleMirror) must:
     1. Call super().__init__(objectId, args, guiRenderer) first.
     2. Create self.qObject (the underlying QGraphicsItem), with its geometry
        CENTERED ON THE LOCAL ORIGIN (e.g. a rect spanning -w/2..w/2, -h/2..h/2).
        The transform model relies on this: setPos places the center, and
        rotation/scale pivot about the origin (which is the center).
     3. Override _applyExtent() to rebuild that centered geometry from
        _width/_height, and call it once after creating qObject.

   The legacy corner-based handlers (_setPosition / _setSize / _setRotation) remain
   for shapes not yet migrated to the transform model; _setTransform / _setExtent are
   the new path.  Because Python resolves 'self.method' through the MRO when the
   _commandHandlers dict is built, any subclass override of _applyExtent (or _setSize)
   is used automatically without needing to re-register the handler.
   """

   @property
   def qObject(self):
      return self._qObject

   @qObject.setter
   def qObject(self, qObject):
      """
      Sets the underlying QGraphicsItem and links it back to this mirror so
      that _QtGraphicsItemEventMixin can resolve self → mirror in O(1)
      via self._mirror.  Pushes the cached visibility so items created with a
      non-default visibility appear at the correct opacity immediately.
      """
      self._qObject = qObject
      if qObject is not None:
         qObject._mirror = self
         self._applyVisibility()

   def __init__(self, objectId, args, guiRenderer):
      self.objectId      = objectId
      self.guiRenderer   = guiRenderer
      self._qObject      = None     # hidden store for qObject property
      self.qZValue       = 0.0      # assigned when added to a Display/Group

      # cached object values, used as fallbacks
      self._localCornerX = 0       # legacy corner-based position (pre-migration shapes)
      self._localCornerY = 0
      self._cx           = 0.0     # center, relative to parent (transform model)
      self._cy           = 0.0
      self._sx           = 1.0     # scale factor x (negative == horizontal flip)
      self._sy           = 1.0     # scale factor y (negative == vertical flip)
      self._width        = 0
      self._height       = 0
      self._rotation     = 0
      self._visibility   = max(0, min(100, int(args.get('visibility', 100))))
      self._toolTipText  = None

      # GuiRenderer only handles commands that alter an object visually.
      # Hit testing (contains/intersects/encloses) is handled entirely in gui.py.
      self._commandHandlers = {
         'setPosition':      self._setPosition,
         'setSize':          self._setSize,
         'setRotation':      self._setRotation,
         'setTransform':     self._setTransform,
         'setExtent':        self._setExtent,
         'setVisibility':    self._setVisibility,
         'setToolTipText':   self._setToolTipText,
         'show':             self._show,
         'hide':             self._hide,
      }

   # ── Position ───────────────────────────────────────────────────────────────

   def handleCommand(self, action, args, responseId):
      """
      Dispatches an incoming command to the appropriate handler method.
      Unknown actions are silently ignored.
      """
      handler = self._commandHandlers.get(action)
      if handler is not None:
         handler(args, responseId)

   # ── Position ───────────────────────────────────────────────────────────────

   def _setPosition(self, args, responseId):
      """
      Set the item's local (x, y) coordinates.
      """
      x = args.get('x', self._localCornerX)
      y = args.get('y', self._localCornerY)

      # update Qt object
      self.qObject.setPos(x, y)

      # cache position for later
      self._localCornerX = x
      self._localCornerY = y

   # ── Size ───────────────────────────────────────────────────────────────────

   def _setSize(self, args, responseId):
      """
      Base size handler — updates _width/_height only.
      Concrete classes override this to also update their QGraphicsItem geometry.
      """
      self._width  = args.get('width',  self._width)
      self._height = args.get('height', self._height)

   # ── Rotation ───────────────────────────────────────────────────────────────

   def _setRotation(self, args, responseId):
      """
      Applies rotation to the Qt object.
      We always rotate around the center of the shape.
      """
      rotation = args.get('rotation', self._rotation)
      centerX  = (self._width  / 2)
      centerY  = (self._height / 2)

      # update internal rotation
      self._rotation = rotation

      # update Qt scene
      qtDegree = -rotation % 360   # CP increases CCW; Qt increases CW
      self.qObject.setTransformOriginPoint(centerX, centerY)
      self.qObject.prepareGeometryChange()
      self.qObject.setRotation(qtDegree)

   # ── Transform / Extent (scene-graph model) ──────────────────────────────────
   # gui.py sends each object's LOCAL transform (center, rotation, scale) relative to
   # its parent, and we mirror the hierarchy (children parented to their Group's
   # QGraphicsItem), so Qt composes the scene transform itself.  Geometry is centered
   # on the local origin, so setPos places the center and rotation/scale pivot there.

   def _setTransform(self, args, responseId):
      """
      Applies this object's local transform: center (cx, cy), rotation, and scale.
      """
      self._cx       = args.get('cx',       self._cx)
      self._cy       = args.get('cy',       self._cy)
      self._rotation = args.get('rotation', self._rotation)
      self._sx       = args.get('sx',       self._sx)
      self._sy       = args.get('sy',       self._sy)
      self._applyTransform()

   def _applyTransform(self):
      """
      Pushes the cached local transform to the Qt item.  Builds a single QTransform
      for rotation + scale about the origin (scale first, then rotation, to match
      gui.py's T . R . S), and uses setPos for the center translation.
      """
      t = QtGui.QTransform()
      t.rotate(-self._rotation)        # gui.py degrees are CCW; Qt is CW under y-down
      t.scale(self._sx, self._sy)
      self.qObject.setTransformOriginPoint(0, 0)   # geometry is centered at the origin
      self.qObject.setTransform(t)
      self.qObject.setPos(self._cx, self._cy)

   def _setExtent(self, args, responseId):
      """
      Updates this object's unrotated, unscaled extent and rebuilds its geometry.
      """
      self._width  = args.get('width',  self._width)
      self._height = args.get('height', self._height)
      self.qObject.prepareGeometryChange()
      self._applyExtent()

   def _applyExtent(self):
      """
      Rebuilds the backing QGraphicsItem's centered-at-origin geometry from
      _width/_height (e.g. a rect spanning -w/2..w/2, -h/2..h/2).  Concrete shape
      mirrors override this; the base does nothing.
      """
      pass

   # ── Visibility ─────────────────────────────────────────────────────────────

   def _show(self, args, responseId):
      """Ensures the item is being drawn."""
      self.qObject.setVisible(True)

   def _hide(self, args, responseId):
      """Ensures the item is not being drawn."""
      self.qObject.setVisible(False)

   def _applyVisibility(self):
      """
      Pushes self._visibility to the qObject's opacity.
      Must be called after self.qObject is created.
      """
      self.qObject.setOpacity(self._visibility / 100.0)

   def _setVisibility(self, args, responseId):
      self._visibility = max(0, min(100, int(args.get('visibility', 100))))
      self._applyVisibility()

   # ── Tooltip ────────────────────────────────────────────────────────────────

   def _setToolTipText(self, args, responseId):
      """
      Sets this item's tooltip (mouseover) text.
      Used by the Display's mouseMove event (via QtView).
      """
      self._toolTipText = args.get('text')


#######################################################################################
# _GraphicsMirror  —  base mirror for shape primitives
#######################################################################################

class _GraphicsMirror(_DrawableMirror):
   """
   Extends _DrawableMirror with color, fill, and line-thickness support.
   All concrete shape classes (RectangleMirror, OvalMirror, etc.) extend this.

   Constructor extracts 'color', 'fill', and 'thickness' from the
   args dict and stores them.  The concrete class is responsible for creating
   qObject and then calling _applyColor() and _applyThickness() to push the
   initial values to Qt.
   """

   def __init__(self, objectId, args, guiRenderer):
      super().__init__(objectId, args, guiRenderer)

      self._color     = args.get('color',     [0, 0, 0, 255])
      self._fill      = args.get('fill',      False)
      self._thickness = args.get('thickness', 1)

      # add graphics-specific command handlers on top of drawable ones
      self._commandHandlers.update({
         'setColor':     self._setColor,
         'setFill':      self._setFill,
         'setThickness': self._setThickness,
      })

   def _applyColor(self):
      """
      Pushes self._color to the QPen outline and, if filled, to the QBrush fill.
      Must be called after self.qObject is created.
      """
      r, g, b, a = self._color
      qColor     = QtGui.QColor(r, g, b, a)

      qPen = self.qObject.pen()
      qPen.setColor(qColor)
      self.qObject.setPen(qPen)

      if self._fill:
         qBrush = QtGui.QBrush(qColor)
      else:
         qBrush = QtGui.QBrush(QtGui.QColor(0, 0, 0, 0))   # fully transparent
      self.qObject.setBrush(qBrush)

   def _applyThickness(self):
      """
      Pushes self._thickness to the QPen line width.
      Must be called after self.qObject is created.
      """
      qPen = self.qObject.pen()
      qPen.setWidth(self._thickness)
      self.qObject.setPen(qPen)

   # ── Color ──────────────────────────────────────────────────────────────────

   def _setColor(self, args, responseId):
      self._color = args.get('color', [0, 0, 0, 255])
      self._applyColor()

   # ── Fill ───────────────────────────────────────────────────────────────────

   def _setFill(self, args, responseId):
      self._fill = bool(args.get('fill', False))
      self._applyColor()   # brush depends on fill state, so re-apply color

   # ── Thickness ──────────────────────────────────────────────────────────────

   def _setThickness(self, args, responseId):
      self._thickness = int(args.get('thickness', 1))
      self._applyThickness()


#######################################################################################
# RectangleMirror  —  mirror of gui.py's Rectangle
#######################################################################################

class RectangleMirror(_GraphicsMirror):
   """
   Mirror of gui.py's Rectangle.  Backed by a QGraphicsRectItem centered on its
   local origin, so setPos places the center and rotation/scale pivot there.

   Constructor args expected in the 'args' dict:
     cx, cy        — center, relative to parent
     width, height — unrotated, unscaled extent
     rotation      — degrees (CCW visual, 0 = no rotation)
     sx, sy        — scale factors (negative == flip)
     color         — [r, g, b, a]
     fill          — bool
     thickness     — int (line width)
     visibility    - percentage (0-100, 0 = transparent)
   """

   def __init__(self, objectId, args, guiRenderer):
      super().__init__(objectId, args, guiRenderer)

      self._cx       = args.get('cx',       0.0)
      self._cy       = args.get('cy',       0.0)
      self._width    = args.get('width',    100)
      self._height   = args.get('height',   100)
      self._rotation = args.get('rotation', 0)
      self._sx       = args.get('sx',       1.0)
      self._sy       = args.get('sy',       1.0)

      # backing Qt item; geometry is built centered on the origin by _applyExtent
      self.qObject = _QRectItem(0, 0, 0, 0)

      self._applyColor()
      self._applyThickness()
      self._applyExtent()      # build the centered rect from width/height
      self._applyTransform()   # place, rotate, and scale about the center

   def _applyExtent(self):
      """Rebuilds the QRectF centered on the origin (spans -w/2..w/2, -h/2..h/2)."""
      w, h = self._width, self._height
      self.qObject.setRect(-w / 2.0, -h / 2.0, w, h)


#######################################################################################
# OvalMirror  —  mirror of gui.py's Oval
#######################################################################################

class OvalMirror(_GraphicsMirror):
   """
   Mirror of gui.py's Oval.  Backed by a QGraphicsEllipseItem centered on its local
   origin, so setPos places the center and rotation/scale pivot there.  Also used by
   Circle and Point.

   Constructor args expected in the 'args' dict:
     cx, cy        — center, relative to parent
     width, height — unrotated, unscaled extent
     rotation      — degrees (CCW visual, 0 = no rotation)
     sx, sy        — scale factors (negative == flip)
     color         — [r, g, b, a]
     fill          — bool
     thickness     — int (line width)
     visibility    - percentage (0-100, 0 = transparent)
   """

   def __init__(self, objectId, args, guiRenderer):
      super().__init__(objectId, args, guiRenderer)

      self._cx       = args.get('cx',       0.0)
      self._cy       = args.get('cy',       0.0)
      self._width    = args.get('width',    100)
      self._height   = args.get('height',   100)
      self._rotation = args.get('rotation', 0)
      self._sx       = args.get('sx',       1.0)
      self._sy       = args.get('sy',       1.0)

      # backing Qt item; geometry is built centered on the origin by _applyExtent
      self.qObject = _QEllipseItem(0, 0, 0, 0)

      self._applyColor()
      self._applyThickness()
      self._applyExtent()      # build the centered ellipse from width/height
      self._applyTransform()   # place, rotate, and scale about the center

   def _applyExtent(self):
      """Rebuilds the ellipse centered on the origin (spans -w/2..w/2, -h/2..h/2)."""
      w, h = self._width, self._height
      self.qObject.setRect(-w / 2.0, -h / 2.0, w, h)


#######################################################################################
# ArcMirror  —  mirror of gui.py's Arc
#######################################################################################

class ArcMirror(_GraphicsMirror):
   """
   Mirror of gui.py's Arc.  Backed by a QGraphicsPathItem whose path is centered on the
   local origin, so setPos places the center and rotation/scale pivot there.  Also used
   by ArcCircle.

   Constructor args expected in the 'args' dict:
     cx, cy        — center, relative to parent
     width, height — unrotated, unscaled extent
     startAngle    — degrees
     endAngle      — degrees
     style         — 0 (PIE), 1 (OPEN), or 2 (CHORD)
     sx, sy        — scale factors (negative == flip)
     color         — [r, g, b, a]
     fill          — bool
     thickness     — int (line width)
     rotation      — degrees (CCW visual, 0 = no rotation)
     visibility    - percentage (0-100, 0 = transparent)
   """

   def __init__(self, objectId, args, guiRenderer):
      super().__init__(objectId, args, guiRenderer)

      self._cx       = args.get('cx',       0.0)
      self._cy       = args.get('cy',       0.0)
      self._width    = args.get('width',    100)
      self._height   = args.get('height',   100)
      self._rotation = args.get('rotation', 0)
      self._sx       = args.get('sx',       1.0)
      self._sy       = args.get('sy',       1.0)

      self._startAngle = args.get('startAngle', 180)
      self._endAngle   = args.get('endAngle',   360)
      self._style      = args.get('style',      _OPEN)
      self._arcWidth   = -(self._endAngle - self._startAngle)  # Qt angles are opposite

      self._commandHandlers.update({
         'setArcWidth': self._setArcWidth,
      })

      self.qObject = _QPathItem(self._buildPath(self._width, self._height))

      self._applyColor()
      self._applyThickness()
      self._applyTransform()   # place, rotate, and scale about the center

   def _buildPath(self, width, height):
      """
      Builds a QPainterPath for the arc, centered on the origin so the item's center
      sits at (0, 0).
      """
      left = -width  / 2
      top  = -height / 2
      path = QtGui.QPainterPath()
      path.arcMoveTo(left, top, width, height, self._startAngle)
      path.arcTo(left, top, width, height, self._startAngle, self._arcWidth)

      if self._style == _PIE:
         path.lineTo(0, 0)        # the center, now the origin
         path.closeSubpath()
      elif self._style == _CHORD:
         path.closeSubpath()

      return path

   def _applyExtent(self):
      """Rebuilds the arc path at the current size, centered on the origin."""
      self.qObject.setPath(self._buildPath(self._width, self._height))

   def _setArcWidth(self, args, responseId):
      """
      Changes the arc's sweep angle and rebuilds the path.
      'arcWidth' uses Qt's sign convention: negative values sweep clockwise.
      """
      self._arcWidth = args.get('arcWidth', self._arcWidth)
      self.qObject.prepareGeometryChange()
      self.qObject.setPath(self._buildPath(self._width, self._height))


#######################################################################################
# LineMirror  —  mirror of gui.py's Line
#######################################################################################

class LineMirror(_GraphicsMirror):
   """
   Mirror of gui.py's Line.  Backed by a QGraphicsLineItem.

   Separated from PolylineMirror because QGraphicsLineItem is simpler and faster
   than QGraphicsPathItem for a two-point line.  It also has a direct setLine() API
   which makes setLength support trivial.

   QGraphicsLineItem has no brush, so _applyColor is overridden to skip setBrush().

   Constructor args expected in the 'args' dict:
     cx, cy        — center, relative to parent
     xPoints       — [x1, x2] endpoint x-coords, relative to the center
     yPoints       — [y1, y2] endpoint y-coords, relative to the center
     rotation      — degrees (CCW visual, 0 = no rotation)
     sx, sy        — scale factors (negative == flip)
     color         — [r, g, b, a]
     thickness     — int (line width)
     visibility    - percentage (0-100, 0 = transparent)
   """

   def __init__(self, objectId, args, guiRenderer):
      super().__init__(objectId, args, guiRenderer)

      self._cx       = args.get('cx',       0.0)
      self._cy       = args.get('cy',       0.0)
      self._rotation = args.get('rotation', 0)
      self._sx       = args.get('sx',       1.0)
      self._sy       = args.get('sy',       1.0)

      # endpoints relative to the center, so the line is centered on the origin
      self._xPoints = args.get('xPoints', [0, 0])
      self._yPoints = args.get('yPoints', [0, 0])
      x1, x2 = self._xPoints
      y1, y2 = self._yPoints

      self.qObject = _QLineItem(x1, y1, x2, y2)

      self._commandHandlers['setPoints'] = self._setPoints

      self._applyColor()
      self._applyThickness()
      self._applyTransform()   # place, rotate, and scale about the center

   def _applyColor(self):
      """
      Overrides _GraphicsMirror._applyColor.
      QGraphicsLineItem has no brush, so we only set the pen color.
      """
      r, g, b, a = self._color
      qColor = QtGui.QColor(r, g, b, a)
      qPen   = self.qObject.pen()
      qPen.setColor(qColor)
      self.qObject.setPen(qPen)

   def _setPoints(self, args, responseId):
      """
      Replaces the line's endpoints (given relative to the center, centered on the
      origin).  Used by gui.py's setLength().
      """
      self._xPoints = args.get('xPoints', self._xPoints)
      self._yPoints = args.get('yPoints', self._yPoints)
      x1, x2 = self._xPoints
      y1, y2 = self._yPoints
      self.qObject.prepareGeometryChange()
      self.qObject.setLine(x1, y1, x2, y2)


#######################################################################################
# PolylineMirror  —  mirror of gui.py's Polyline
#######################################################################################

class PolylineMirror(_GraphicsMirror):
   """
   Mirror of gui.py's Polyline.  Backed by a QGraphicsPathItem.

   Constructor args expected in the 'args' dict:
     cx, cy        — center, relative to parent
     xPoints       — x-coordinates of the points, relative to the center
     yPoints       — y-coordinates of the points, relative to the center
     rotation      — degrees (CCW visual, 0 = no rotation)
     sx, sy        — scale factors (negative == flip)
     color         — [r, g, b, a]
     thickness     — int (line width)
     visibility    - percentage (0-100, 0 = transparent)
   """

   def __init__(self, objectId, args, guiRenderer):
      super().__init__(objectId, args, guiRenderer)

      self._cx       = args.get('cx',       0.0)
      self._cy       = args.get('cy',       0.0)
      self._rotation = args.get('rotation', 0)
      self._sx       = args.get('sx',       1.0)
      self._sy       = args.get('sy',       1.0)

      # points relative to the center, so the shape is centered on the origin
      self._xPoints = args.get('xPoints', [0, 0])
      self._yPoints = args.get('yPoints', [0, 0])

      self.qObject = _QPathItem(self._buildPath(self._xPoints, self._yPoints))

      self._commandHandlers['setPoints'] = self._setPoints

      self._applyColor()
      self._applyThickness()
      self._applyTransform()   # place, rotate, and scale about the center

   def _buildPath(self, xPoints, yPoints):
      """Builds a QPainterPath through the given local points."""
      path = QtGui.QPainterPath()
      path.moveTo(xPoints[0], yPoints[0])
      for i in range(1, len(xPoints)):
         path.lineTo(xPoints[i], yPoints[i])
      return path

   def _setPoints(self, args, responseId):
      """Replaces the polyline's points (given relative to the center)."""
      self._xPoints = args.get('xPoints', self._xPoints)
      self._yPoints = args.get('yPoints', self._yPoints)
      self.qObject.prepareGeometryChange()
      self.qObject.setPath(self._buildPath(self._xPoints, self._yPoints))


#######################################################################################
# PolygonMirror  —  mirror of gui.py's Polygon
#######################################################################################

class PolygonMirror(_GraphicsMirror):
   """
   Mirror of gui.py's Polygon.  Backed by a QGraphicsPolygonItem.

   Constructor args expected in the 'args' dict:
     cx, cy        — center, relative to parent
     xPoints       — x-coordinates of the points, relative to the center
     yPoints       — y-coordinates of the points, relative to the center
     rotation      — degrees (CCW visual, 0 = no rotation)
     sx, sy        — scale factors (negative == flip)
     color         — [r, g, b, a]
     fill          — bool
     thickness     — int (line width)
     visibility    - percentage (0-100, 0 = transparent)
   """

   def __init__(self, objectId, args, guiRenderer):
      super().__init__(objectId, args, guiRenderer)

      self._cx       = args.get('cx',       0.0)
      self._cy       = args.get('cy',       0.0)
      self._rotation = args.get('rotation', 0)
      self._sx       = args.get('sx',       1.0)
      self._sy       = args.get('sy',       1.0)

      # points relative to the center, so the shape is centered on the origin
      self._xPoints = args.get('xPoints', [0, 0, 0])
      self._yPoints = args.get('yPoints', [0, 0, 0])

      self.qObject = _QPolygonItem(self._buildPolygon(self._xPoints, self._yPoints))

      self._commandHandlers['setPoints'] = self._setPoints

      self._applyColor()
      self._applyThickness()
      self._applyTransform()   # place, rotate, and scale about the center

   def _buildPolygon(self, xPoints, yPoints):
      """Builds a QPolygonF through the given local points."""
      polygon = QtGui.QPolygonF()
      for i in range(len(xPoints)):
         polygon.append(QtCore.QPointF(xPoints[i], yPoints[i]))
      return polygon

   def _setPoints(self, args, responseId):
      """Replaces the polygon's points (given relative to the center)."""
      self._xPoints = args.get('xPoints', self._xPoints)
      self._yPoints = args.get('yPoints', self._yPoints)
      self.qObject.prepareGeometryChange()
      self.qObject.setPolygon(self._buildPolygon(self._xPoints, self._yPoints))


#######################################################################################
# IconMirror  —  mirror of gui.py's Icon
#######################################################################################


def _qColorFromChannels(channels):
   """Builds a QColor from a [r, g, b] or [r, g, b, a] list, defaulting alpha to fully
   opaque (255) when the alpha channel is omitted."""
   red, green, blue = channels[0], channels[1], channels[2]
   alpha = channels[3] if len(channels) > 3 else 255
   return QtGui.QColor(red, green, blue, alpha)


class IconMirror(_GraphicsMirror):
   """
   Mirror of gui.py's Icon.  Backed by a QGraphicsPixmapItem.

   Unlike other mirrors, Icon does most of its work on the Qt side because pixel
   operations must happen where the QPixmap lives.  This means IconMirror has
   getters (getPixel, getPixels) that send responses back through the pipe.

   Extends _GraphicsMirror for rotation support.  Overrides _applyColor to
   flood-fill the pixmap (since QGraphicsPixmapItem has no brush to recolor)
   and _applyThickness as a no-op (no pen either).

   Constructor args expected in the 'args' dict:
     filename   — path to image file (str)
     width      — optional target width (int or None)
     height     — optional target height (int or None)
     rotation   — degrees (CCW)
     visibility - percentage (0-100, 0 = transparent)
   """

   def __init__(self, objectId, args, guiRenderer):
      super().__init__(objectId, args, guiRenderer)

      filename = args.get('filename', '')
      width    = args.get('width')
      height   = args.get('height')

      # build pixmap
      pixmap = QtGui.QPixmap(filename)

      if pixmap.isNull():
         # file failed to load — create blank pixmap
         if width is None:
            width = 600
         if height is None:
            height = 400
         pixmap = QtGui.QPixmap(width, height)

      # resolve width/height from pixmap if not specified
      if width is None and height is None:
         width  = pixmap.width()
         height = pixmap.height()
      elif width is None:
         width = int(pixmap.width() * (height / pixmap.height()))
      elif height is None:
         height = int(pixmap.height() * (width / pixmap.width()))

      self._pixmap = pixmap   # original (unscaled) pixmap for quality rescaling
      self._width  = width
      self._height = height
      self._cx       = args.get('cx',       0.0)
      self._cy       = args.get('cy',       0.0)
      self._rotation = args.get('rotation', 0)
      self._sx       = args.get('sx',       1.0)
      self._sy       = args.get('sy',       1.0)

      self.qObject = _QPixmapItem()

      # add Icon-specific command handlers
      self._commandHandlers.update({
         'getSize':   self._getSize,
         'crop':      self._crop,
         'getPixel':  self._getPixel,
         'setPixel':  self._setPixel,
         'getPixels': self._getPixels,
         'setPixels': self._setPixels,
         'write':     self._write,
      })

      self._applyColor()
      self._applyExtent()      # scale the pixmap to size and center it on the origin
      self._applyTransform()   # place, rotate, and scale about the center

   def _applyColor(self):
      """
      Overrides _GraphicsMirror._applyColor.  Floods every pixel of self._pixmap with
      self._color — including its alpha channel — so the icon becomes a solid block of
      that color and the original image's own transparency (silhouette) is discarded.
      The fill is permanent — self._pixmap is updated in place — so later _setSize
      rescales keep the new color.

      Fully-transparent colors (alpha 0, including the default Color.CLEAR) are skipped:
      this lets construction (and the inherited _setFill) leave the icon in its original
      colors.  Use setVisibility(0) to hide an Icon by transparency.
      """
      r, g, b, a = self._color
      if a > 0:
         image = QtGui.QImage(self._pixmap.size(), QtGui.QImage.Format.Format_ARGB32)
         image.fill(QtGui.QColor(r, g, b, a))

         self._pixmap = QtGui.QPixmap.fromImage(image)
         self.qObject.setPixmap(self._pixmap.scaled(self._width, self._height))

   def _applyThickness(self):
      """No-op — QGraphicsPixmapItem has no pen or brush."""
      pass

   # ── Size ───────────────────────────────────────────────────────────────────

   def _getSize(self, args, responseId):
      """
      Returns [width, height] for this item.
      Used to resolve dimensions after creation, since pixel data lives in Qt.
      """
      self.guiRenderer.sendResponse(responseId, [self._width, self._height])

   def _applyExtent(self):
      """
      Scales the pixmap from the original to the current size and centers it on the
      origin, so the item's transform turns and scales it about its center.
      """
      width  = max(1, int(self._width))
      height = max(1, int(self._height))
      scaledPixmap = self._pixmap.scaled(width, height)
      self.qObject.setPixmap(scaledPixmap)
      self.qObject.setOffset(-width / 2.0, -height / 2.0)

   # ── Crop ───────────────────────────────────────────────────────────────────

   def _crop(self, args, responseId):
      """
      Crops the original pixmap to the given rectangle, then recenters it on the origin.
      """
      x      = args.get('x', 0)
      y      = args.get('y', 0)
      width  = args.get('width',  self._width)
      height = args.get('height', self._height)

      self._pixmap = self._pixmap.copy(x, y, width, height)
      self._width  = width
      self._height = height
      self.qObject.prepareGeometryChange()
      self._applyExtent()

   # ── Pixel getters / setters ────────────────────────────────────────────────

   def _getPixel(self, args, responseId):
      """
      Returns [r, g, b, a] for the pixel at (column, row) on the original pixmap.
      """
      column = args.get('column', 0)
      row    = args.get('row', 0)
      image  = self._pixmap.toImage()
      color  = image.pixelColor(column, row)
      self.guiRenderer.sendResponse(responseId, [color.red(), color.green(), color.blue(), color.alpha()])

   def _setPixel(self, args, responseId):
      """
      Sets the pixel at (column, row) to [r, g, b] or [r, g, b, a] on the original pixmap
      (alpha defaults to opaque), then rescales to current display dimensions.
      """
      column = args.get('column', 0)
      row    = args.get('row', 0)
      color  = args.get('color', [0, 0, 0])

      image = self._pixmap.toImage().convertToFormat(QtGui.QImage.Format.Format_ARGB32)
      image.setPixelColor(column, row, _qColorFromChannels(color))
      self._pixmap = QtGui.QPixmap.fromImage(image)

      scaledPixmap = self._pixmap.scaled(self._width, self._height)
      self.qObject.setPixmap(scaledPixmap)

   def _getPixels(self, args, responseId):
      """
      Returns all pixels as a 2D list of [r, g, b, a] values from the original pixmap.
      """
      image  = self._pixmap.toImage()
      image  = image.convertToFormat(QtGui.QImage.Format.Format_RGBA8888)
      width  = image.width()
      height = image.height()

      pixels = []
      for row in range(height):
         rowPixels = []
         for col in range(width):
            color = image.pixelColor(col, row)
            rowPixels.append([color.red(), color.green(), color.blue(), color.alpha()])
         pixels.append(rowPixels)

      self.guiRenderer.sendResponse(responseId, pixels)

   def _setPixels(self, args, responseId):
      """
      Sets all pixels from a 2D list of [r, g, b] or [r, g, b, a] values (alpha defaults
      to opaque).  Rebuilds the pixmap and rescales to current display dimensions.
      """
      pixels = args.get('pixels', [])
      if not pixels:
         return

      height = len(pixels)
      width  = len(pixels[0])

      image = QtGui.QImage(width, height, QtGui.QImage.Format.Format_RGBA8888)
      for row in range(height):
         for col in range(width):
            image.setPixelColor(col, row, _qColorFromChannels(pixels[row][col]))

      self._pixmap = QtGui.QPixmap.fromImage(image)
      scaledPixmap = self._pixmap.scaled(self._width, self._height)
      self.qObject.setPixmap(scaledPixmap)

   # ── Write ──────────────────────────────────────────────────────────────────

   def _write(self, args, responseId):
      """
      Saves the icon's original pixmap to a file.
      Optional width/height args resize the output; omitting one preserves aspect ratio.
      Sends [success (bool), resolvedPath (str)] back to the parent process.
      """
      import os
      filename = args.get('filename', 'icon.png')
      width    = args.get('width')
      height   = args.get('height')

      pixmap = self._pixmap

      if width is not None or height is not None:
         origW  = pixmap.width()
         origH  = pixmap.height()
         width  = int(origW * (height / origH)) if width  is None else int(width)
         height = int(origH * (width  / origW)) if height is None else int(height)
         pixmap = pixmap.scaled(width, height,
                                QtCore.Qt.AspectRatioMode.IgnoreAspectRatio,
                                QtCore.Qt.TransformationMode.SmoothTransformation)

      success      = pixmap.save(filename)
      resolvedPath = os.path.abspath(filename)
      self.guiRenderer.sendResponse(responseId, [success, resolvedPath])


#######################################################################################
# LabelMirror  —  mirror of gui.py's Label
#######################################################################################

class LabelMirror(_GraphicsMirror):
   """
   Mirror of gui.py's Label.  Backed by a QGraphicsItemGroup containing
   a QGraphicsTextItem (foreground text) and a QGraphicsRectItem (background).

   Overrides _applyColor (text color), _applyThickness (background pen), and
   _setFill (background visibility) because Label's Qt structure differs from
   simple shape items.

   Constructor args expected in the 'args' dict:
     text             — string
     alignment        — int (Qt.AlignmentFlag value: 1=Left, 132=Center, 2=Right)
     textColor        — [r, g, b, a]
     backgroundColor  — [r, g, b, a]
     font             — None or [name, [weight, italic], size]
     visibility       - percentage (0-100, 0 = transparent)
   """

   def __init__(self, objectId, args, guiRenderer):
      super().__init__(objectId, args, guiRenderer)

      text            = str(args.get('text', ''))
      alignment       = args.get('alignment', 1)   # 1 = AlignLeft
      textColor       = args.get('textColor', [0, 0, 0, 255])
      backgroundColor = args.get('backgroundColor', [0, 0, 0, 0])
      font            = args.get('font')

      self._color           = textColor
      self._backgroundColor = backgroundColor
      self._cx       = args.get('cx',       0.0)
      self._cy       = args.get('cy',       0.0)
      self._rotation = args.get('rotation', 0)
      self._sx       = args.get('sx',       1.0)
      self._sy       = args.get('sy',       1.0)

      # foreground text
      self._qTextObject = QtWidgets.QGraphicsTextItem(text)
      r, g, b, a = textColor
      self._qTextObject.setDefaultTextColor(QtGui.QColor(r, g, b, a))

      # background rectangle behind the text
      self._qBackgroundObject = QtWidgets.QGraphicsRectItem()
      r, g, b, a = backgroundColor
      self._qBackgroundObject.setBrush(QtGui.QColor(r, g, b, a))
      self._qBackgroundObject.setPen(QtCore.Qt.PenStyle.NoPen)

      # the label is a group holding the background and the text together
      self.qObject = _QGroupItem()
      self.qObject.setHandlesChildEvents(False)
      self.qObject.addToGroup(self._qBackgroundObject)
      self.qObject.addToGroup(self._qTextObject)

      self._setAlignmentValue(alignment)
      if font is not None:
         self._applyFont(font)

      self._layoutCentered()   # size from the text bounds and center the content
      self._applyTransform()   # place, rotate, and scale about the center

      # add Label-specific command handlers
      self._commandHandlers.update({
         'getSize':            self._getSize,
         'setText':            self._setText,
         'setBackgroundColor': self._setBackgroundColor,
         'setAlignment':       self._setAlignment,
         'setFont':            self._setFont,
      })

   # ── Overrides ──────────────────────────────────────────────────────────────

   def _applyColor(self):
      """Sets the text color (not pen/brush — Labels use setDefaultTextColor)."""
      r, g, b, a = self._color
      self._qTextObject.setDefaultTextColor(QtGui.QColor(r, g, b, a))

   def _applyThickness(self):
      """Sets the background rectangle's pen width."""
      qPen = self._qBackgroundObject.pen()
      qPen.setWidth(self._thickness)
      self._qBackgroundObject.setPen(qPen)

   def _setFill(self, args, responseId):
      """Controls background visibility.  When unfilled, background is transparent."""
      self._fill = bool(args.get('fill', False))
      if self._fill:
         r, g, b, a = self._backgroundColor
         qColor = QtGui.QColor(r, g, b, a)
      else:
         qColor = QtGui.QColor(0, 0, 0, 0)
      self._qBackgroundObject.setBrush(QtGui.QBrush(qColor))

   # ── Size ───────────────────────────────────────────────────────────────────

   def _getSize(self, args, responseId):
      """
      Returns [width, height] for this item.
      Used to resolve dimensions after creation, since pixel data lives in Qt.
      """
      self.guiRenderer.sendResponse(responseId, [self._width, self._height])

   # ── Text ───────────────────────────────────────────────────────────────────

   def _setText(self, args, responseId):
      """Sets the label's text and re-centers it to its new bounds."""
      text = str(args.get('text', ''))
      self._qTextObject.setPlainText(text)
      self.qObject.prepareGeometryChange()
      self._layoutCentered()

   def _layoutCentered(self):
      """
      Takes the size from the text bounds and centers both the text and its background
      rectangle on the origin, so the label's transform turns and scales it about its
      center.
      """
      bounds = self._qTextObject.boundingRect()
      width  = bounds.width()
      height = bounds.height()
      self._width  = int(width)
      self._height = int(height)
      self._qTextObject.setPos(-width / 2.0, -height / 2.0)
      self._qBackgroundObject.setRect(-width / 2.0, -height / 2.0, width, height)

   # ── Background color ──────────────────────────────────────────────────────

   def _setBackgroundColor(self, args, responseId):
      """Sets the background rectangle's fill color."""
      self._backgroundColor = args.get('color', [0, 0, 0, 0])
      r, g, b, a = self._backgroundColor
      self._qBackgroundObject.setBrush(QtGui.QColor(r, g, b, a))

   # ── Alignment ──────────────────────────────────────────────────────────────

   def _setAlignment(self, args, responseId):
      """Sets text alignment from an integer Qt.AlignmentFlag value."""
      alignment = args.get('alignment', 1)
      self._setAlignmentValue(alignment)

   def _setAlignmentValue(self, alignment):
      """Applies alignment to the text item's document."""
      qtFlag      = QtCore.Qt.AlignmentFlag(alignment)
      document    = self._qTextObject.document()
      textOption  = document.defaultTextOption()
      textOption.setAlignment(qtFlag)
      document.setDefaultTextOption(textOption)

   # ── Font ───────────────────────────────────────────────────────────────────

   def _setFont(self, args, responseId):
      """Sets the text font from [name, [weight, italic], size], then re-centers."""
      font = args.get('font')
      if font is not None:
         self._applyFont(font)
         self.qObject.prepareGeometryChange()
         self._layoutCentered()

   def _applyFont(self, font):
      """Constructs a QFont and applies it to the text item."""
      name, style, size = font
      weight, italic    = style
      qFont = QtGui.QFont(name, size)
      qFont.setWeight(QtGui.QFont.Weight(weight))
      qFont.setItalic(italic)
      self._qTextObject.setFont(qFont)


#######################################################################################
# GroupMirror  —  mirror of gui.py's Group
#######################################################################################

class GroupMirror(_DrawableMirror):
   """
   Mirror of gui.py's Group.  Backed by a QGraphicsItemGroup.

   Groups contain other drawable mirrors as children.  Adding a child attaches
   its qObject to this group's QGraphicsItemGroup; removing detaches it.

   Group extends _DrawableMirror (not _GraphicsMirror) because gui.py's Group
   inherits from _Drawable, not _Graphics — it has no color, fill, or thickness.

   Constructor args expected in the 'args' dict:
     (none — children are added via addChild / addChildOrder commands)
   """

   def __init__(self, objectId, args, guiRenderer):
      super().__init__(objectId, args, guiRenderer)

      self.qObject = _QGroupItem()
      self.qObject.setHandlesChildEvents(False)   # children deliver their own events
      self._itemList = []
      # the group has no geometry of its own; its transform arrives via setTransform
      # and Qt composes it onto the children parented under it.

      # add Group-specific command handlers
      self._commandHandlers.update({
         'addChild':      self._addChild,
         'addChildOrder': self._addChildOrder,
         'removeChild':   self._removeChild,
         'removeAll':     self._removeAll,
         'getOrder':      self._getOrder,
         'setOrder':      self._setOrder,
      })

   # ── Child management ───────────────────────────────────────────────────────

   def _addChild(self, args, responseId):
      """Adds a child at the top of the z-order (order = 0)."""
      itemId          = args.get('itemId')
      addChildArgs    = {'itemId': itemId, 'order': 0}
      self._addChildOrder(addChildArgs, responseId=None)

   def _addChildOrder(self, args, responseId):
      """
      Parents a child under this group at the given z-order.  The child's transform
      (relative to the group) arrives separately via setTransform; Qt composes the
      group's transform onto it, so there is nothing to position here.
      """
      itemId = args.get('itemId')
      order  = args.get('order', 0)

      item = self.guiRenderer._objectRegistry.get(itemId)
      if item is None:
         return

      # remove from this group if already present
      if item in self._itemList:
         self._itemList.remove(item)

      # clamp order and insert
      order = max(0, min(len(self._itemList), order))
      self._itemList.insert(order, item)

      # calculate z-value (same algorithm as DisplayMirror)
      if order == 0:
         qZValue = 1.0
         if len(self._itemList) > 1:
            neighbor = self._itemList[1]
            qZValue  = neighbor.qZValue + 1.0

      elif order >= len(self._itemList) - 1:
         qZValue = 0.0
         if len(self._itemList) > 1:
            neighbor = self._itemList[-2]
            qZValue  = neighbor.qZValue - 1.0

      else:
         frontNeighbor = self._itemList[order - 1]
         backNeighbor  = self._itemList[order + 1]
         qZValue       = (frontNeighbor.qZValue + backNeighbor.qZValue) / 2.0

      item.qZValue = qZValue
      item.qObject.setZValue(qZValue)

      # detach from any previous parent/scene, then add to this group.  addToGroup (not
      # setParentItem) is used so the QGraphicsItemGroup keeps a bounding area over its
      # children, which is what lets the group receive cascaded mouse events.  Its
      # position adjustment is harmless: the child's own setTransform follows and
      # overwrites it.
      _detachItem(item)
      self.qObject.addToGroup(item.qObject)

   def _removeChild(self, args, responseId):
      """Detaches a child from the group; it is removed from the scene entirely."""
      itemId = args.get('itemId')
      item   = self.guiRenderer._objectRegistry.get(itemId)
      if item is not None and item in self._itemList:
         self._itemList.remove(item)
         _detachItem(item)

   def _removeAll(self, args, responseId):
      """Detaches every child from the group; each is removed from the scene entirely."""
      for item in list(self._itemList):
         _detachItem(item)
      self._itemList.clear()

   def _getOrder(self, args, responseId):
      """Returns the order of a child in the group."""
      itemId = args.get('itemId')
      order  = None
      for i, item in enumerate(self._itemList):
         if item.objectId == itemId:
            order = i
            break
      self.guiRenderer.sendResponse(responseId, [order])

   def _setOrder(self, args, responseId):
      """Changes a child's z-order by removing and re-adding at the new position."""
      itemId         = args.get('itemId')
      order          = args.get('order', 0)
      addChildArgs   = {'itemId': itemId, 'order': order}
      self._addChildOrder(addChildArgs, responseId=None)


#######################################################################################
# _ControlMirror  —  base mirror for all Control widgets
#######################################################################################

class _ControlMirror(_DrawableMirror):
   """
   Base class for all Control mirror objects (QWidgets, not QGraphicsItems).
   Overrides methods that require special handling for QWidgets:
   - position: setPos() -> move()
   - dimensions: setRect(), setPath(), etc. -> setFixedSize()
   - color: [r, g, b] -> stylesheets

   Controls handle their own input directly via Qt's widget event system.

   Concrete classes must:
     1. Call super().__init__(objectId, args, guiRenderer) first.
     2. Create self.qObject (the underlying QWidget).
   """

   @_DrawableMirror.qObject.setter
   def qObject(self, qObject):
      """
      Overrides _DrawableMirror.qObject.setter to skip the _mirror backlink
      (QWidgets don't use _QtGraphicsItemEventMixin), while still pushing the
      cached visibility through _applyVisibility.
      """
      self._qObject = qObject
      if qObject is not None:
         self._applyVisibility()

   def __init__(self, objectId, args, guiRenderer):
      _DrawableMirror.__init__(self, objectId, args, guiRenderer)

      # add Control-specific command handlers
      self._commandHandlers.update({
         'getSize' : self._getSize
      })

   # ── Placement (a QWidget can move and resize, but not rotate or scale) ────────

   def _applyTransform(self):
      """
      Moves the widget so its center lands at (cx, cy).  Rotation and scale do not
      apply to a native widget, so they are ignored.
      """
      left = int(round(self._cx - self._width / 2))
      top  = int(round(self._cy - self._height / 2))
      self.qObject.move(left, top)

   # ── Visibility ─────────────────────────────────────────────────────────────

   def _applyVisibility(self):
      """
      Overrides _DrawableMirror._applyVisibility for QWidgets.
      QWidget has no setOpacity(); a QGraphicsOpacityEffect attached to the
      widget is the standard way to fade it uniformly.  The effect is created
      lazily on first apply and reused thereafter.
      """
      effect = self.qObject.graphicsEffect()
      if not isinstance(effect, QtWidgets.QGraphicsOpacityEffect):
         effect = QtWidgets.QGraphicsOpacityEffect(self.qObject)
         self.qObject.setGraphicsEffect(effect)
      effect.setOpacity(self._visibility / 100.0)

   # ── Size ───────────────────────────────────────────────────────────────────

   def _getSize(self, args, responseId):
      self.guiRenderer.sendResponse(responseId, [self._width, self._height])

   def _setExtent(self, args, responseId):
      """
      Overrides _DrawableMirror._setExtent: a QWidget has no prepareGeometryChange()
      (that is a QGraphicsItem call), and setFixedSize handles the geometry update.
      """
      self._width  = int(args.get('width',  self._width))
      self._height = int(args.get('height', self._height))
      self._applyExtent()

   def _applyExtent(self):
      """
      Forces the widget to its current size, then re-places it (since we position a
      widget by its center, its top-left depends on its size).
      """
      width  = max(1, int(self._width))
      height = max(1, int(self._height))
      self.qObject.setFixedSize(width, height)
      self._applyTransform()

   # ── Event helper ───────────────────────────────────────────────────────────

   def _forwardEvent(self, eventType, eventArgs=None):
      """
      Checks if the event is registered, and if so, sends it to the parent process.
      Connected to Qt signals in the concrete class constructor.
      """
      isRegistered = (self.objectId, eventType) in self.guiRenderer._registeredEvents
      if isRegistered:
         self.guiRenderer.sendEvent(eventType, self.objectId, eventArgs or {})


#######################################################################################
# ButtonMirror  —  mirror of gui.py's Button
#######################################################################################

class ButtonMirror(_ControlMirror):
   """
   Mirror of gui.py's Button.  Backed by a QPushButton.

   Constructor args expected in the 'args' dict:
     text   — string
     color  — [r, g, b, a]
   """

   def __init__(self, objectId, args, guiRenderer):
      super().__init__(objectId, args, guiRenderer)

      text  = args.get('text', '')
      color = args.get('color', [211, 211, 211, 255])   # LIGHT_GRAY default

      self.qObject = QtWidgets.QPushButton()
      self.qObject.setText(text)
      self.qObject.adjustSize()
      self._width  = self.qObject.width()
      self._height = self.qObject.height()

      self._applyColor(color)

      # wire Qt signal → event forwarding
      self.qObject.clicked.connect(lambda: self._forwardEvent('clicked'))

      # add Button-specific command handlers
      self._commandHandlers.update({
         'setText':  self._setText,
         'getText':  self._getText,
         'setColor': self._setColor,
      })

   def _applyColor(self, color):
      r, g, b, a = color
      dr = max(0, int(r * 0.9))
      dg = max(0, int(g * 0.9))
      db = max(0, int(b * 0.9))
      self.qObject.setStyleSheet(
         f"QPushButton {{ background-color: rgba({r},{g},{b},{a}); color: black; }}"
         f"QPushButton::pressed {{ background-color: rgba({dr},{dg},{db},{a}); }}"
      )

   def _setColor(self, args, responseId):
      color = args.get('color', [211, 211, 211, 255])
      self._applyColor(color)

   def _setText(self, args, responseId):
      text = args.get('text', '')
      self.qObject.setText(text)
      self.qObject.adjustSize()
      self._width  = self.qObject.width()
      self._height = self.qObject.height()

   def _getText(self, args, responseId):
      self.guiRenderer.sendResponse(responseId, [self.qObject.text()])


#######################################################################################
# CheckBoxMirror  —  mirror of gui.py's CheckBox
#######################################################################################

class CheckBoxMirror(_ControlMirror):
   """
   Mirror of gui.py's CheckBox.  Backed by a QCheckBox.

   Constructor args expected in the 'args' dict:
     text   — string
     color  — [r, g, b, a]
   """

   def __init__(self, objectId, args, guiRenderer):
      super().__init__(objectId, args, guiRenderer)

      text  = args.get('text', '')
      color = args.get('color', [0, 0, 0, 0])   # CLEAR default

      self.qObject = QtWidgets.QCheckBox(text)
      self.qObject.adjustSize()
      self._width  = self.qObject.width()
      self._height = self.qObject.height()

      self._applyColor(color)

      self.qObject.stateChanged.connect(
         lambda state: self._forwardEvent('stateChanged', {'checked': state != 0})
      )

      self._commandHandlers.update({
         'setText':    self._setText,
         'getText':    self._getText,
         'setColor':   self._setColor,
         'isChecked':  self._isChecked,
         'check':      self._check,
         'uncheck':    self._uncheck,
      })

   def _applyColor(self, color):
      r, g, b, a = color
      self.qObject.setStyleSheet(
         f"QCheckBox {{ background-color: rgba({r},{g},{b},{a}); color: black; }}"
      )

   def _setColor(self, args, responseId):
      color = args.get('color', [0, 0, 0, 0])
      self._applyColor(color)

   def _setText(self, args, responseId):
      text = args.get('text', '')
      self.qObject.setText(text)
      self.qObject.adjustSize()
      self._width  = self.qObject.width()
      self._height = self.qObject.height()

   def _getText(self, args, responseId):
      self.guiRenderer.sendResponse(responseId, [self.qObject.text()])

   def _isChecked(self, args, responseId):
      self.guiRenderer.sendResponse(responseId, [self.qObject.isChecked()])

   def _check(self, args, responseId):
      self.qObject.setChecked(True)

   def _uncheck(self, args, responseId):
      self.qObject.setChecked(False)


#######################################################################################
# SliderMirror  —  mirror of gui.py's Slider
#######################################################################################

class SliderMirror(_ControlMirror):
   """
   Mirror of gui.py's Slider.  Backed by a QSlider.

   Constructor args expected in the 'args' dict:
     orientation  — int (1 = Horizontal, 2 = Vertical; matches Qt.Orientation values)
     minValue     — int
     maxValue     — int
     startValue   — int
   """

   def __init__(self, objectId, args, guiRenderer):
      super().__init__(objectId, args, guiRenderer)

      orientation = args.get('orientation', 1)   # 1 = Horizontal
      minValue    = args.get('minValue', 0)
      maxValue    = args.get('maxValue', 100)
      startValue  = args.get('startValue')
      color       = args.get('color', [211, 211, 211, 255])   # LIGHT_GRAY default

      if startValue is None:
         startValue = int((minValue + maxValue) / 2)

      self._orientation = orientation
      qtOrientation = QtCore.Qt.Orientation(orientation)
      self.qObject = QtWidgets.QSlider(qtOrientation)
      self.qObject.setRange(minValue, maxValue)
      self.qObject.setValue(startValue)
      self.qObject.adjustSize()
      self._width  = self.qObject.width()
      self._height = self.qObject.height()

      self._applyColor(color)

      # wire Qt signal → event forwarding
      self.qObject.valueChanged.connect(
         lambda value: self._forwardEvent('valueChanged', {'value': value})
      )

      self._commandHandlers.update({
         'setValue':  self._setValue,
         'getValue':  self._getValue,
         'setColor':  self._setColor,
      })

   def _applyColor(self, color):
      r, g, b, a = color
      fill = f"rgba({r},{g},{b},{a})"
      if self._orientation == 2:   # vertical: the filled part below the handle is add-page
         self.qObject.setStyleSheet(
            f"QSlider::groove:vertical {{ width: 6px; background: #c8c8c8; border-radius: 3px; }}"
            f"QSlider::add-page:vertical {{ background: {fill}; border-radius: 3px; }}"
            f"QSlider::handle:vertical {{ background: {fill}; height: 14px; margin: 0 -5px; border-radius: 7px; }}"
         )
      else:                        # horizontal: the filled part left of the handle is sub-page
         self.qObject.setStyleSheet(
            f"QSlider::groove:horizontal {{ height: 6px; background: #c8c8c8; border-radius: 3px; }}"
            f"QSlider::sub-page:horizontal {{ background: {fill}; border-radius: 3px; }}"
            f"QSlider::handle:horizontal {{ background: {fill}; width: 14px; margin: -5px 0; border-radius: 7px; }}"
         )

   def _setColor(self, args, responseId):
      color = args.get('color', [211, 211, 211, 255])
      self._applyColor(color)

   def _setValue(self, args, responseId):
      value = args.get('value', 0)
      self.qObject.setValue(value)

   def _getValue(self, args, responseId):
      self.guiRenderer.sendResponse(responseId, [self.qObject.value()])


#######################################################################################
# DropDownListMirror  —  mirror of gui.py's DropDownList
#######################################################################################

class DropDownListMirror(_ControlMirror):
   """
   Mirror of gui.py's DropDownList.  Backed by a QComboBox.

   Constructor args expected in the 'args' dict:
     items  — list of strings
     color  — [r, g, b, a]
   """

   def __init__(self, objectId, args, guiRenderer):
      super().__init__(objectId, args, guiRenderer)

      items = args.get('items', [])
      color = args.get('color', [211, 211, 211, 255])   # LIGHT_GRAY default

      self.qObject = QtWidgets.QComboBox()
      self.qObject.addItems(items)
      self.qObject.adjustSize()
      self._width  = self.qObject.width()
      self._height = self.qObject.height()

      self._applyColor(color)

      # wire Qt signal → event forwarding (sends selected index)
      self.qObject.activated.connect(
         lambda index: self._forwardEvent('activated', {'index': index})
      )

      self._commandHandlers.update({
         'setColor': self._setColor,
      })

   def _applyColor(self, color):
      r, g, b, a = color
      self.qObject.setStyleSheet(
         f"QComboBox {{ background-color: rgba({r},{g},{b},{a}); color: black; }}"
         f"QComboBox QAbstractItemView {{ background-color: rgba({r},{g},{b},{a}); color: black; }}"
      )

   def _setColor(self, args, responseId):
      color = args.get('color', [211, 211, 211, 255])
      self._applyColor(color)


#######################################################################################
# TextFieldMirror  —  mirror of gui.py's TextField
#######################################################################################

class TextFieldMirror(_ControlMirror):
   """
   Mirror of gui.py's TextField.  Backed by a QLineEdit.

   Constructor args expected in the 'args' dict:
     text    — string
     width   — int (pre-computed by gui.py from columns + font metrics)
     height  — int (pre-computed by gui.py)
     color   — [r, g, b, a]
     font    — None or [name, [weight, italic], size]
   """

   def __init__(self, objectId, args, guiRenderer):
      super().__init__(objectId, args, guiRenderer)

      text   = args.get('text', '')
      width  = args.get('width')
      height = args.get('height')
      color  = args.get('color', [255, 255, 255, 255])   # WHITE default
      font   = args.get('font')

      self.qObject = QtWidgets.QLineEdit(str(text))

      if font is not None:
         self._applyFont(font)

      columns = args.get('columns')

      if width is not None and height is not None:
         self.qObject.setFixedSize(width, height)
         self._width  = width
         self._height = height
      elif columns is not None:
         fm       = QtGui.QFontMetrics(self.qObject.font())
         charW    = fm.horizontalAdvance('M')
         charH    = fm.lineSpacing()
         margins  = self.qObject.textMargins()
         hMargin  = margins.left() + margins.right()
         vMargin  = margins.top()  + margins.bottom()
         frameOpt = QtWidgets.QStyleOptionFrame()
         self.qObject.initStyleOption(frameOpt)
         frame    = self.qObject.style().pixelMetric(
            QtWidgets.QStyle.PixelMetric.PM_DefaultFrameWidth, frameOpt, self.qObject
         )
         w = (charW * columns) + hMargin + (2 * frame)
         h = charH + vMargin + (2 * frame)
         self.qObject.setFixedSize(w, h)
         self._width  = w
         self._height = h
      else:
         self.qObject.adjustSize()
         self._width  = self.qObject.width()
         self._height = self.qObject.height()

      self._applyColor(color)

      # wire Qt signal → event forwarding
      self.qObject.returnPressed.connect(
         lambda: self._forwardEvent('returnPressed', {'text': self.qObject.text()})
      )

      self._commandHandlers.update({
         'setText':  self._setText,
         'getText':  self._getText,
         'setColor': self._setColor,
         'setFont':  self._setFont,
      })

   def _applyColor(self, color):
      r, g, b, a = color
      self.qObject.setStyleSheet(
         f"QLineEdit {{ background-color: rgba({r},{g},{b},{a}); color: black; }}"
      )

   def _setColor(self, args, responseId):
      color = args.get('color', [255, 255, 255, 255])
      self._applyColor(color)

   def _setText(self, args, responseId):
      text = args.get('text', '')
      self.qObject.setText(text)

   def _getText(self, args, responseId):
      self.guiRenderer.sendResponse(responseId, [self.qObject.text()])

   def _applyFont(self, font):
      name, style, size = font
      weight, italic    = style
      qFont = QtGui.QFont(name, size)
      qFont.setWeight(QtGui.QFont.Weight(weight))
      qFont.setItalic(italic)
      self.qObject.setFont(qFont)

   def _setFont(self, args, responseId):
      font = args.get('font')
      if font is not None:
         self._applyFont(font)


#######################################################################################
# TextAreaMirror  —  mirror of gui.py's TextArea
#######################################################################################

class TextAreaMirror(_ControlMirror):
   """
   Mirror of gui.py's TextArea.  Backed by a QTextEdit.

   Constructor args expected in the 'args' dict:
     text    — string
     width   — int (pre-computed by gui.py from columns/rows + font metrics)
     height  — int (pre-computed by gui.py)
     color   — [r, g, b, a]
     font    — None or [name, [weight, italic], size]
   """

   def __init__(self, objectId, args, guiRenderer):
      super().__init__(objectId, args, guiRenderer)

      text   = args.get('text', '')
      width  = args.get('width')
      height = args.get('height')
      color  = args.get('color', [255, 255, 255, 255])   # WHITE default
      font   = args.get('font')

      columns = args.get('columns')
      rows    = args.get('rows')

      self.qObject = QtWidgets.QTextEdit(str(text))

      if font is not None:
         self._applyFont(font)

      if width is not None and height is not None:
         self.qObject.setFixedSize(width, height)
         self._width  = width
         self._height = height
      elif columns is not None or rows is not None:
         fm = QtGui.QFontMetrics(self.qObject.font())
         w  = fm.horizontalAdvance('M') * (columns or 8)
         h  = fm.lineSpacing()          * (rows    or 5)
         self.qObject.setFixedSize(w, h)
         self._width  = w
         self._height = h
      else:
         self.qObject.adjustSize()
         self._width  = self.qObject.width()
         self._height = self.qObject.height()

      self._applyColor(color)

      self._commandHandlers.update({
         'setText':  self._setText,
         'getText':  self._getText,
         'setColor': self._setColor,
         'setFont':  self._setFont,
      })

   def _applyColor(self, color):
      r, g, b, a = color
      self.qObject.setStyleSheet(
         f"QTextEdit {{ background-color: rgba({r},{g},{b},{a}); color: black; }}"
      )

   def _setColor(self, args, responseId):
      color = args.get('color', [255, 255, 255, 255])
      self._applyColor(color)

   def _setText(self, args, responseId):
      text = args.get('text', '')
      self.qObject.setText(text)

   def _getText(self, args, responseId):
      self.guiRenderer.sendResponse(responseId, [self.qObject.toPlainText()])

   def _applyFont(self, font):
      name, style, size = font
      weight, italic    = style
      qFont = QtGui.QFont(name, size)
      qFont.setWeight(QtGui.QFont.Weight(weight))
      qFont.setItalic(italic)
      self.qObject.setFont(qFont)

   def _setFont(self, args, responseId):
      font = args.get('font')
      if font is not None:
         self._applyFont(font)

#######################################################################################
# MenuMirror  —  mirror of gui.py's Menu
#######################################################################################

class MenuMirror:
   """
   Mirror of gui.py's Menu class.  Backed by a QMenu.

   Menus are not placed on a Display via add() — they are attached to a
   Display's menu bar (addMenu command) or used as a right-click context menu
   (addPopupMenu command).

   Constructor args expected in the 'args' dict:
     title — string

   Item callbacks are routed back to gui.py via a single 'itemTriggered' event
   carrying {'itemIndex': int}.  gui.py maps the index to the per-item callback.
   """

   def __init__(self, objectId, args, guiRenderer):
      self.objectId     = objectId
      self.guiRenderer = guiRenderer

      title       = args.get('title', '')
      self._qMenu = QtWidgets.QMenu(title)

      self._commandHandlers = {
         'addItem':      self._addItem,
         'addSeparator': self._addSeparator,
         'addSubmenu':   self._addSubmenu,
         'enable':       self._enable,
         'disable':      self._disable,
      }

   def handleCommand(self, action, args, responseId):
      handler = self._commandHandlers.get(action)
      if handler is not None:
         handler(args, responseId)

   def _addItem(self, args, responseId):
      text      = args.get('text', '')
      itemIndex = args.get('itemIndex', 0)
      qAction   = QtGui.QAction(text, self._qMenu)
      qAction.triggered.connect(
         lambda checked=False, idx=itemIndex: self._onItemTriggered(idx)
      )
      self._qMenu.addAction(qAction)

   def _onItemTriggered(self, itemIndex):
      isRegistered = (self.objectId, 'itemTriggered') in self.guiRenderer._registeredEvents
      if isRegistered:
         self.guiRenderer.sendEvent('itemTriggered', self.objectId, {'itemIndex': itemIndex})

   def _addSeparator(self, args, responseId):
      self._qMenu.addSeparator()

   def _addSubmenu(self, args, responseId):
      submenuId = args.get('submenuId')
      submenu   = self.guiRenderer._objectRegistry.get(submenuId)
      if submenu is not None:
         self._qMenu.addMenu(submenu._qMenu)

   def _enable(self, args, responseId):
      self._qMenu.setEnabled(True)

   def _disable(self, args, responseId):
      self._qMenu.setEnabled(False)
