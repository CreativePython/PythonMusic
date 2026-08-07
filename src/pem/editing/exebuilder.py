"""The editor's "Create Executable" button: package the current script into a
standalone program the student can share.

This module is only the Tk front end -- confirm with the student, show a
progress dialog with a Cancel button, and report the result.  The actual
PyInstaller build lives in ``pem.build.userscript`` so it can be reused and
tested away from the GUI.
"""

import platform
import threading
from pathlib import Path
from tkinter import messagebox
from tkinter import Toplevel, StringVar
from tkinter.ttk import Progressbar, Label, Button, Frame

from pem.config import pemConf
from pem.build import userscript


class ExeBuilder:
   """Drives one "Create Executable" run for a single editor window."""

   def __init__(self, editwin):
      """Store the editor window whose script we will build.

      Args:
         editwin: EditorWindow, providing io.filename / io.save() / get_saved()
            and top (the window used as the dialog's parent).
      """
      self.editwin = editwin
      self.scriptPath = None

   def create_executable(self):
      """Confirm, then build the current script into a standalone executable."""
      # Make sure there is a saved file on disk to build from.
      if not self._ensure_file_saved():
         return

      # Let the student back out before a multi-minute build starts.
      if not self._confirm_build():
         return

      # PyInstaller is a dependency of PEM, but a pip install could be missing
      # it; check before we promise anything.
      if not self._check_pyinstaller():
         return

      self._run_build()

   def _ensure_file_saved(self):
      """Ensure the current buffer is saved to a file, returning success.

      Prompts for a filename if the buffer was never saved, and auto-saves any
      unsaved edits so we build exactly what the student sees.
      """
      filename = self.editwin.io.filename

      # A brand-new, never-saved buffer: ask where to save it first.
      if not filename:
         self.editwin.io.save(None)
         filename = self.editwin.io.filename
         if not filename:
            # Student cancelled the save dialog.
            return False

      # Unsaved edits: write them out so the build matches the editor.
      if not self.editwin.get_saved():
         self.editwin.io.save(None)

      self.scriptPath = Path(filename).resolve()
      return True

   def _confirm_build(self):
      """Ask the student to confirm the build, returning their choice."""
      system = platform.system()
      if system == "Windows":
         resultDescription = f"{self.scriptPath.stem}.exe"
      elif system == "Darwin":
         resultDescription = f"{self.scriptPath.stem}.app (plus a .tar.gz to share)"
      else:
         resultDescription = self.scriptPath.stem

      message = (
         f"Create a standalone program from {self.scriptPath.name}?\n\n"
         f"This makes {resultDescription} in the same folder as your script, "
         f"which you can share with others on the same kind of computer.\n\n"
         f"Building can take a few minutes."
      )
      return messagebox.askyesno(
         title="Create Executable",
         message=message,
         parent=self.editwin.text,
      )

   def _check_pyinstaller(self):
      """Return True if PyInstaller can be imported, else explain how to get it."""
      try:
         import PyInstaller  # noqa: F401
         return True
      except ImportError:
         messagebox.showerror(
            title="PyInstaller Not Found",
            message=(
               "Creating an executable needs the PyInstaller package.\n\n"
               "Install it from a terminal with:\n\n"
               "    pip install pyinstaller"
            ),
            parent=self.editwin.text,
         )
         return False

   def _show_console_preference(self):
      """Return the student's "Show Console" choice for built executables."""
      return pemConf.GetOption(
         "main", "CreateExecutable", "console",
         type="bool", default=False, warn_on_default=False,
      )

   def _quit_on_window_close_preference(self):
      """Return the student's "Quit When Last Window Closes" choice."""
      return pemConf.GetOption(
         "main", "CreateExecutable", "quit-on-window-close",
         type="bool", default=True, warn_on_default=False,
      )

   def _run_build(self):
      """Run the build on a background thread, driving a modal progress dialog.

      The dialog stays responsive and offers Cancel; when the worker finishes we
      show a success or failure message.  Tk is single-threaded, so the worker
      never touches widgets directly -- it hands its result back and we poll for
      it from the Tk event loop.
      """
      console = self._show_console_preference()
      quitOnWindowClose = self._quit_on_window_close_preference()
      cancelEvent = threading.Event()
      progressDialog = ProgressDialog(self.editwin.top, on_cancel=cancelEvent.set)

      # Filled in by the worker thread; read by the Tk-side poller below.
      resultBox = []
      latestStatus = ["Preparing the build..."]

      def report(statusText):
         # Called from the worker thread -- just stash the text; the poller
         # copies it onto the widget on the Tk thread.
         latestStatus[0] = statusText

      def worker():
         try:
            result = userscript.build_user_executable(
               self.scriptPath,
               console=console,
               quit_on_window_close=quitOnWindowClose,
               progress=report,
               cancel_event=cancelEvent,
            )
         except Exception as error:
            result = userscript.BuildResult(
               False, message=f"Something went wrong while building:\n\n{error}"
            )
         resultBox.append(result)

      buildThread = threading.Thread(target=worker, daemon=True)
      buildThread.start()

      # Poll from the Tk event loop so the dialog keeps painting and the Cancel
      # button stays clickable while the worker runs.
      def poll():
         progressDialog.update_status(latestStatus[0])
         if resultBox:
            progressDialog.close()
            self._report_result(resultBox[0])
         else:
            self.editwin.top.after(100, poll)

      self.editwin.top.after(100, poll)

   def _report_result(self, result):
      """Show the outcome of a finished build to the student."""
      if result.cancelled:
         # Nothing to say -- the student asked us to stop.
         return

      if result.success:
         messagebox.showinfo(
            title="Executable Created",
            message=result.message,
            parent=self.editwin.text,
         )
      else:
         messagebox.showerror(
            title="Couldn't Create Executable",
            message=result.message,
            parent=self.editwin.text,
         )


class ProgressDialog:
   """A small modal dialog showing build progress, with a Cancel button."""

   def __init__(self, parent, on_cancel=None):
      """Build and show the dialog.

      Args:
         parent: The window to center on and block.
         on_cancel: Called (once) when the student clicks Cancel.
      """
      self.on_cancel = on_cancel
      self.cancelled = False

      self.dialog = Toplevel(parent)
      self.dialog.title("Creating Executable")
      self.dialog.resizable(False, False)

      # Modal: sit above the editor and take input until the build ends.
      self.dialog.transient(parent)
      self.dialog.grab_set()
      # Treat the window-close button the same as Cancel.
      self.dialog.protocol("WM_DELETE_WINDOW", self._cancel)

      body = Frame(self.dialog, padding=20)
      body.pack(fill="both", expand=True)

      self.statusVar = StringVar(master=self.dialog, value="Preparing the build...")
      Label(body, textvariable=self.statusVar, wraplength=340).pack(
         anchor="w", pady=(0, 10))

      self.progress = Progressbar(body, mode="indeterminate", length=340)
      self.progress.pack(fill="x")
      self.progress.start(12)

      self.cancelButton = Button(body, text="Cancel", command=self._cancel)
      self.cancelButton.pack(anchor="e", pady=(14, 0))

      self._center_on(parent)

   def _center_on(self, parent):
      """Position the dialog over the middle of its parent window."""
      self.dialog.update_idletasks()
      width = self.dialog.winfo_width()
      height = self.dialog.winfo_height()
      x = parent.winfo_x() + (parent.winfo_width() - width) // 2
      y = parent.winfo_y() + (parent.winfo_height() - height) // 2
      self.dialog.geometry(f"+{x}+{y}")

   def _cancel(self):
      """Handle a Cancel click (or window close): tell the build to stop, once."""
      if self.cancelled:
         return
      self.cancelled = True
      self.statusVar.set("Cancelling...")
      self.cancelButton.configure(state="disabled")
      if self.on_cancel is not None:
         self.on_cancel()

   def update_status(self, message):
      """Show a new status line (unless the student is cancelling)."""
      if not self.cancelled:
         self.statusVar.set(message)

   def close(self):
      """Stop the animation and dismiss the dialog."""
      try:
         self.progress.stop()
         self.dialog.grab_release()
         self.dialog.destroy()
      except Exception:
         pass
