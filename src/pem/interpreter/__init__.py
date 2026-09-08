"""Running the user's code.

``Interpreter`` is the object the rest of PEM talks to: a window asks it to run
or stop something and it handles the subprocesses, start to finish.  How it
does that -- the process pair, the RPC socket, the code that runs on the far
side -- is this package's own business.

    from pem.interpreter import Interpreter

``manager`` holds the object itself, ``rpc`` the socket layer it talks over,
``run`` the server running inside each subprocess, and ``startup`` the
interpreter settings each subprocess applies before the user's code runs.
"""
from pem.interpreter.manager import Interpreter

__all__ = ['Interpreter']
