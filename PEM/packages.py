"""
packages.py -- compatibility shim.

The real build configuration now lives in the shipped package at
``src/pem/build/packages.py`` so the editor's "Create Executable" feature can
read it in every install mode (source, pip, frozen).  This shim keeps
``build.py``'s ``from packages import ...`` working -- including during the
pre-venv bootstrap, before PythonMusic is installed -- by pointing at the
in-tree source copy and re-exporting everything from it.
"""

import os
import sys

# Make the in-tree ``pem`` package importable without requiring an install:
# this file lives in PEM/, and the source tree is at PEM/../src.
_SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, "src"))
if _SRC not in sys.path:
   sys.path.insert(0, _SRC)

from pem.build.packages import *  # noqa: F401,F403
# Names build.py imports directly (``import *`` skips those a module lists in
# __all__, and defensively names them so the import contract stays explicit).
from pem.build.packages import (  # noqa: F401
   CORE_LIBRARIES,
   EXTRA_PACKAGES,
   CORE_EXCLUDES,
   TESTING_EXCLUDES,
   DATA_SCIENCE_EXCLUDES,
   PYSIDE6_EXCLUDES,
   BUILD_PROFILES,
   getExcludes,
   getExcludesByCategory,
)
