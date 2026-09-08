"""Text-encoding settings shared by PEM's editor I/O and the execution
subprocess's stdio.

Kept in its own tiny module so the execution subprocess (``pem.interpreter.run``)
can import just these constants without pulling in ``iomenu`` -- which would
drag in tkinter and the whole config system.  ``iomenu`` re-exports the same
names for backward compatibility.
"""
import sys

# How shell <-> subprocess text streams are decoded/encoded.
encoding = 'utf-8'
# Round-trip non-UTF-8 bytes (e.g. lone surrogates from the OS) instead of
# raising.  surrogatepass on Windows, surrogateescape elsewhere.
errors = 'surrogatepass' if sys.platform == 'win32' else 'surrogateescape'
