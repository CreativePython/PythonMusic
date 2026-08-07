"""
packages.py

Centralized PyInstaller package configuration for PEM builds.

This module provides lists of different packages for inclusion in build.py and PEM's create executable function.

It lives inside the shipped ``pem`` package so both the PEM application build
(PEM/build.py, via a thin shim) and the editor's "Create Executable" feature
(pem.editing.exebuilder) read the exact same lists in every install mode --
running from source, pip-installed, or frozen.
"""

# PythonMusic's core libraries, and the specific modules needed to run them.
CORE_LIBRARIES = [
   "gui", "music", "midi", "osc", "timer", "utilities",
   "iannix", "markov", "zipf", "image",
   "PythonMusic.RealtimeAudioPlayer",
   "PythonMusic.notationRenderer",
   "PySide6.QtCore", "PySide6.QtGui", "PySide6.QtWidgets", "PySide6.QtOpenGL", "PySide6.QtOpenGLWidgets",
   "mido.backends.rtmidi", "mido.backends.portmidi",
   "matplotlib.pyplot", "numpy"
]

# Additional python libraries to install and bundle (focused on beginner-friendly packages)
# Libraries are mapped from their pip package name -> list of python import names
EXTRA_PACKAGES = {
   "regex" : ["regex"]
}

# Core packages to always exclude (never needed in executables)
CORE_EXCLUDES = [
   'jupyter',      # Jupyter notebook environment
   'IPython',      # Interactive Python shell
   'notebook',     # Jupyter notebook interface
   'torch',        # PyTorch (very large, rarely needed)
]

# Testing frameworks (never needed in production executables)
TESTING_EXCLUDES = [
   'pytest',       # pytest testing framework
   # 'unittest',     # Python unittest (stdlib but can be excluded)
   'nose',         # nose testing framework
   'tox',          # tox test automation
]

# Heavy data science packages (exclude unless explicitly imported)
DATA_SCIENCE_EXCLUDES = [
   'matplotlib',   # plotting library
   'scipy',        # scientific computing
   'pandas',       # data analysis
   'sklearn',      # scikit-learn machine learning
]

# PySide6 modules unused by PythonMusic
# PythonMusic only uses: QtCore, QtGui, QtWidgets, QtOpenGLWidgets
# Excluding these saves 400+ MB per executable
PYSIDE6_EXCLUDES = [
   # 3D Graphics (not used)
   'PySide6.Qt3DAnimation',
   'PySide6.Qt3DCore',
   'PySide6.Qt3DExtras',
   'PySide6.Qt3DInput',
   'PySide6.Qt3DLogic',
   'PySide6.Qt3DRender',

   # Web & Network (not used)
   'PySide6.QtWebEngineCore',
   'PySide6.QtWebEngineQuick',
   'PySide6.QtWebEngineWidgets',
   'PySide6.QtWebChannel',
   'PySide6.QtWebSockets',
   'PySide6.QtWebView',
   'PySide6.QtNetworkAuth',
   'PySide6.QtHttpServer',
   'PySide6.QtNetwork',   # osc.py uses Python socket, not Qt

   # Data Visualization (not used)
   'PySide6.QtCharts',
   'PySide6.QtDataVisualization',
   'PySide6.QtGraphs',
   'PySide6.QtGraphsWidgets',

   # Multimedia (not used)
   'PySide6.QtMultimedia',
   'PySide6.QtMultimediaWidgets',
   'PySide6.QtSpatialAudio',

   # QML/Quick (not used)
   'PySide6.QtQml',
   'PySide6.QtQuick',
   'PySide6.QtQuick3D',
   'PySide6.QtQuickControls2',
   'PySide6.QtQuickTest',
   'PySide6.QtQuickWidgets',

   # PDF (not used)
   'PySide6.QtPdf',
   'PySide6.QtPdfWidgets',

   # Hardware/IoT (not used)
   'PySide6.QtBluetooth',
   'PySide6.QtNfc',
   'PySide6.QtSensors',
   'PySide6.QtSerialBus',
   'PySide6.QtSerialPort',
   'PySide6.QtLocation',
   'PySide6.QtPositioning',

   # Database (not used)
   'PySide6.QtSql',

   # Designer/Development (not needed in executables)
   'PySide6.QtDesigner',
   'PySide6.QtUiTools',
   'PySide6.QtHelp',
   'PySide6.QtTest',

   # Other unused modules
   'PySide6.QtAxContainer',
   'PySide6.QtConcurrent',
   'PySide6.QtDBus',
   'PySide6.QtExampleIcons',
   'PySide6.QtOpenGL',      # we use QtOpenGLWidgets instead
   'PySide6.QtPrintSupport',
   'PySide6.QtRemoteObjects',
   'PySide6.QtScxml',
   'PySide6.QtStateMachine',
   'PySide6.QtSvg',
   'PySide6.QtSvgWidgets',
   'PySide6.QtTextToSpeech',
   'PySide6.QtXml',
]

# Build profiles for different use cases
BUILD_PROFILES = {
   'pem_app': {
      # Full PEM application - be more conservative
      # Exclude only core packages that are never needed
      'general': CORE_EXCLUDES + TESTING_EXCLUDES,
      'pyside6': PYSIDE6_EXCLUDES,  # Still exclude unused PySide6 to save space
   },
   'user_script': {
      # User-created executables - optimize for size
      # Exclude everything that's not explicitly needed
      'general': CORE_EXCLUDES + TESTING_EXCLUDES + DATA_SCIENCE_EXCLUDES,
      'pyside6': PYSIDE6_EXCLUDES,
   },
}


def getExcludes(profile='user_script'):
   """
   Get appropriate exclusions for the specified build profile.

   Args:
      profile (str): Build profile name. Options:
         - 'pem_app': For building the full PEM application
         - 'user_script': For building user-created executables (default)

   Returns:
      list: Combined list of all modules to exclude for this profile

   Example:
      >>> excludes = getExcludes('user_script')
      >>> for module in excludes:
      ...     command.extend(['--exclude-module', module])
   """
   if profile not in BUILD_PROFILES:
      raise ValueError(f"Unknown build profile: {profile}. "
                      f"Valid options: {list(BUILD_PROFILES.keys())}")

   config = BUILD_PROFILES[profile]
   all_excludes = config['general'] + config['pyside6']
   return all_excludes


def getExcludesByCategory(profile='user_script'):
   """
   Get exclusions organized by category for more granular control.

   Args:
      profile (str): Build profile name

   Returns:
      dict: Dictionary with 'general' and 'pyside6' exclusion lists

   Example:
      >>> exclusions = getExcludesByCategory('pem_app')
      >>> for module in exclusions['general']:
      ...     command.extend(['--exclude-module', module])
      >>> for module in exclusions['pyside6']:
      ...     command.extend(['--exclude-module', module])
   """
   if profile not in BUILD_PROFILES:
      raise ValueError(f"Unknown build profile: {profile}")

   return BUILD_PROFILES[profile].copy()
