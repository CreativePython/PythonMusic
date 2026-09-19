# build.py
#
# Convenience script that builds PEM executable using PyInstaller.
# This script can only build for the OS/architecture it runs in (Windows, MacOS-ARM, MacOS-Intel, etc.).
# The only requirement is that the machine has Python 3.12+ installed.
#
# This script will bootstrap a Python Virtual Environment as part of the build process.
# If you have PythonMusic and PyInstaller installed, you can skip bootstrapping
# using the argument "--in-venv" (e.g. 'python build.py --in-venv')

import os, sys, platform, shutil, time, tomllib
from pathlib import Path
from packages import CORE_LIBRARIES, EXTRA_PACKAGES, CORE_EXCLUDES, TESTING_EXCLUDES, PYSIDE6_EXCLUDES

appName = "PEM"                              # executable name
system  = platform.system()                     # target operating system
if system == "Darwin":
   system = "MacOS" + "-" + platform.machine()  # append architecture on MacOS

buildPath      = Path(__file__).parent          # PEM's build location
rootPath       = buildPath.parent               # PythonMusic's root directory
venvPath       = buildPath / f".build-venv-{platform.machine()}"      # virtual environment for building
mainScriptPath = buildPath / "PEM.py"        # frozen-build entry point (delegates to the pem package)
specPath       = buildPath / "build" / f"PythonMusic-{system}.spec"  # PyInstaller specifications
tomlPath       = rootPath / "pyproject.toml"

# get version from pyproject.toml
pyproject = tomllib.loads(tomlPath.read_text(encoding="utf-8"))
version = pyproject.get("project", {}).get("version", "").strip()

# soundfont download source and encryption hash
SF2_URL    = "https://www.dropbox.com/s/xixtvox70lna6m2/FluidR3%20GM2-2.SF2?dl=1"
SF2_SHA256 = "2ae766ab5c5deb6f7fffacd6316ec9f3699998cce821df3163e7b10a78a64066"

# bundle the first soundfont (.sf2) found in build location
soundfontFiles = list((buildPath).glob("*.sf2")) \
               + list((buildPath).glob("*.SF2"))
soundfontPath  = soundfontFiles[0] if len(soundfontFiles) > 0 else None

def printd(string):
   "Print but with a small delay, to make it easier to read output stream."
   print(string)
   time.sleep(1.5)


def main():
   print("=" * 40)
   print("PEM Executable Builder")
   print(f"Python Version: {sys.version}")
   printd("=" * 40)

   exitCode = None

   # ensure we're in the correct virtual environment
   environmentSuccess = checkEnvironment()
   if environmentSuccess == False:
      exitCode = buildVirtualEnvironment()

   if exitCode is None:
      # ensure we have necessary files
      requirementsSuccess = checkRequirements()
      if requirementsSuccess == False:
         print("Exiting...")
         exitCode = 1

   if exitCode is None:
      # we have what we need, so build PEM
      runSuccess = runPyInstaller()
      if runSuccess == False:
         print("Exiting...")
         exitCode = 1

   if exitCode is None:
      # finally, output some information about the completed build
      printDetails()
      exitCode = 0

      # # next, build for MacOS Intel if running from a MacOS ARM machine
      # if system == "MacOS-arm64" and ("--in-venv" in sys.argv) and ("--rosetta" not in sys.argv):
      #    rosettaSuccess = runRosetta()
      #    if rosettaSuccess == False:
      #       exitCode = 1

      print("Exiting...")

   return exitCode

##### Primary Methods
def checkEnvironment():
   """Determines whether this script was run in the build environment."""
   return "--in-venv" in sys.argv


def buildVirtualEnvironment():
   """Bootstraps a fresh build environment, then reruns this script in it."""
   import venv, subprocess
   global venvPath

   printd(f"Generating a clean build environment '{str(venvPath)}'")

   # build a fresh virtual environment
   builder = venv.EnvBuilder(with_pip=True, clear=True)
   builder.create(venvPath)

   printd("-" * 40)
   printd("Installing PythonMusic and PyInstaller to build environment.")
   printd("(This may take a few minutes...)")

   # find the virtual environment's python and pip locations
   if system.startswith("Windows"):
      python = str(venvPath / "Scripts" / "python.exe")
      pip    = str(venvPath / "Scripts" / "pip.exe")
   else:
      python = str(venvPath / "bin" / "python")
      pip    = str(venvPath / "bin" / "pip")

   # install PythonMusic and PyInstaller to the new environment
   # Use 'python -m pip' to avoid file locking issues
   subprocess.check_call([python, "-m", "pip", "install", "--quiet", "--upgrade", "pip"])

   subprocess.check_call([pip, "install", "--quiet", "--editable", str(rootPath)])
   printd("OK: Successfully installed PythonMusic.")

   subprocess.check_call([pip, "install", "--quiet", "pyinstaller==6.16.0"])
   print("OK: Successfully installed PyInstaller.")
   printd("-" * 40)

   # install additional packages for inclusion in executable
   printd("Installing additional packages for bundle inclusion...")
   printd("(This may take a few minutes...)")

   # install additional packages (continue on error - some may fail but others should succeed)
   for package in EXTRA_PACKAGES.keys():
      try:
         subprocess.check_call([pip, "install", "--quiet", package])
      except subprocess.CalledProcessError:
         # package failed to install - log but continue
         print(f"Warning: Failed to install {package} (skipping)")

   printd("OK: Finished installing packages.")
   printd("-" * 40)

   # now, call this script again from within the virtual environment
   printd("Restarting in build environment...")
   call = [python, str(Path(__file__)), "--in-venv"]
   if "--include-soundfont" in sys.argv:
      call.append("--include-soundfont")
   exitCode = subprocess.call(call)

   return exitCode


def checkRequirements():
   """Ensures all required files to build PythonMusic are present."""
   from pooch import retrieve
   global specPath, mainScriptPath, buildPath
   global soundfontPath, SF2_URL, SF2_SHA256
   requirementSuccess = True

   print("Checking for necessary files...")
   printd("-" * 40)
   missing = []

   # create .spec file for PyInstaller settings
   printd("Generating PyInstaller specifications...")

   generateSuccess = generateSpecFile()
   if not generateSuccess:
      missing.append(str(specPath))
      printd("Error: Failed to generate PyInstaller specifications.")
   else:
      printd("OK: Successfully generated PyInstaller specifications.")

   # ensure main entry point exists
   printd("Finding application entry point...")

   if not mainScriptPath.exists():
      missing.append(str(mainScriptPath))
      printd("Error: Failed to find application entry point.")
   else:
      printd("OK: Successfully found application entry point.")

   if "--include-soundfont" in sys.argv:
      # ensure soundfont exists, and download one if not
      printd("Finding bundled soundfont...")

      if (soundfontPath is None) or (not soundfontPath.exists()):
         printd("Warning: Failed to find soundfont (.sf2).")
         print("Downloading FluidR3 soundfont...")
         printd("-" * 40)
         soundfontPath = Path(retrieve(                   # download soundfont
            url=SF2_URL,
            known_hash=f"sha256:{SF2_SHA256}",
            progressbar=False,
            path=str(buildPath)
         ))
         printd("-" * 40)

         # check again to make sure download completed
         if (soundfontPath is None) or (not soundfontPath.exists()):
            missing.append(str(buildPath / "*.sf2"))
            print("Error: Failed to download soundfont.")
         else:
            print("OK: Successfully downloaded soundfont.")

      else:
         print("OK: Successfully found soundfont.")

   printd("-" * 40)

   if len(missing) > 0:
      print("Error: Missing necessary files.")
      print()
      print("Please provide missing files to build PEM.")
      for item in missing:
         print(f"\t{item}")
      requirementSuccess = False

   else:
      print("OK: Successfully found all necessary files.")
      requirementSuccess = True

   printd("=" * 40)
   return requirementSuccess


def runPyInstaller():
   """Executes PyInstaller in the bootstrapped environment."""
   import PyInstaller.__main__ as pyi

   global specPath, buildPath
   buildSuccess = True

   distPath = buildPath / "dist" / system
   workPath = buildPath / "build" / system
   # clean output directory (clear contents but keep the directory so PyInstaller has a valid path)
   printd("Cleaning output directory...")

   if distPath.exists():
      for item in distPath.iterdir():
         if item.is_dir():
            shutil.rmtree(str(item))
         else:
            item.unlink()
   else:
      distPath.mkdir(parents=True, exist_ok=True)

   # run PyInstaller
   printd("Running PyInstaller...")
   print("(This may take a few minutes...)")
   print("-" * 40)

   try:
      pyi.run([
         "--clean",
         str(specPath),
         f"--distpath={str(distPath)}",
         f"--workpath={str(workPath)}",
         "--log-level",
         "WARN",
      ])
   except SystemExit as e:
      if e.code == 0:
         buildSuccess = True
      else:
         buildSuccess = False
         print("-" * 40)
         print(f"Error: Build failed with exit code: {e.code}")

   except Exception as e:
      buildSuccess = False
      print("-" * 40)
      print(f"Error: Build failed with error: {e}")

   if buildSuccess:
      print("-" * 40)
      print("OK: Successfully built with PyInstaller.")

   printd("=" * 40)
   return buildSuccess


# def checkRosetta():
#    """(MacOS ARM) Determines whether this machine has Rosetta installed."""
#    return Path("/Library/Apple/usr/libexec/oahd").exists()


# def checkPythonRosetta(py):
#    """(MacOS ARM) Verifies if a given python can run in an Intel (x86_64) environment."""
#    import subprocess
#    try:
#       # attempt to inspect it
#       out = subprocess.check_output(
#          ["arch", "-x86_64", py, "-c",
#          "import platform; print(platform.machine())"],
#          stderr=subprocess.DEVNULL,
#          text=True
#       ).strip()

#    except Exception:
#       out = ""

#    return ("universal" in out) or ("x86_64" in out)


# def checkIntelPython():
#    """(MacOS ARM) Finds an appropriate version of Python to run with Rosetta.  Prefers the current python (provided it's universal), or looks for a compatible python for Intel in the standard installation location '/usr/local/bin/python3'."""
#    py = sys.executable  # get current python

#    if not checkPythonRosetta(py):
#       # the current python isn't Intel-capable, so look for one
#       fallback = "/usr/local/bin/python3"
#       if Path(fallback).exists() and checkPythonRosetta(fallback):
#          # success, found an Intel python
#          py = fallback
#       else:
#          # fail, no Intel python available
#          py = None

#    return py


# def runRosetta():
#    import subprocess

#    py = checkIntelPython()  # get an Intel python interpreter

#    if py is not None:
#       # build with Rosetta terminal
#       cmd = ["arch", "-x86_64", py, str(Path(__file__)), "--rosetta"]

#       # preserve optional flags
#       if "--include-soundfont" in sys.argv:
#          cmd.append("--include-soundfont")

#       printd("Starting Intel (x86_64) build under Rosetta 2...")
#       exitCode = subprocess.call(cmd)
   
#    else:
#       # no Intel python available, so skip
#       printd("Error: Couldn't find an Intel-compatible Python.  Either run this script from a universal2 binary, or use a Rosetta terminal to install Python at '/usr/local/bin/python3' and try again.")
#       exitCode = 1

#    return exitCode


def printDetails():
   """Print information about completed executable."""
   global buildPath, appName, system
   sizeMB  = 0

   if system.startswith("Windows"):  # Windows
      appPath = buildPath / "dist" / system / (appName + ".exe")
      if appPath.exists():
            sizeMB = appPath.stat().st_size / (1024 * 1024)
            printd("Bundling zip...")
            bundleZip()

   elif system.startswith("MacOS"):  # MacOS
      appPath = buildPath / "dist" / system / (appName + ".app")
      if appPath.exists():
         seen = set()
         totalSize = 0

         for f in appPath.rglob('*'):  # for each file in app...
            try:
               st = os.lstat(f)  # get file information
            except OSError:
               st = None

            # skip symlinks and non-files
            if not os.path.isfile(f) or os.path.islink(f):
               st = None

            if st is not None:
               key = (st.st_dev, st.st_ino)  # unique file ID
               if key not in seen:           # aggregate size if not seen
                  seen.add(key)
                  totalSize = totalSize + st.st_size

         sizeMB = totalSize / (1024 * 1024)

         printd("Bundling tarball...")
         bundleTar()

      else:
         print("Error: Expected an app, but none was produced.")
         sizeMB = 0
         # # binary, not .app
         # appPath = buildPath / "dist" / system / (appName)
         # sizeMB = appPath.stat().st_size / (1024 * 1024)

   else:  # Linux, FreeBSD, Jython  (we're not targeting FreeBSD or Jython...)
      appPath = buildPath / "dist" / system / (appName)
      if appPath.exists():
            sizeMB = appPath.stat().st_size / (1024 * 1024)

   print(f"Location:\t{appPath}")
   print(f"Size:\t{sizeMB:.1f} MB")

   printd("=" * 40)


def getDependencies():
   """
   Extract dependencies from a given pyproject.toml file.
   Returns the dependencies as a list of strings.
   """
   global pyproject

   depsData = pyproject.get("project", {}).get("dependencies", []) or []
   depsList = [d for d in depsData if isinstance(d, str)]

   return depsList

def getPEPName(requirement):
   """
   Extracts distribution name from a PEP 508 requirement string.
   e.g. "PySide6>=6.9.1" -> "PySide6"
        "foo-bar[extra]>=1; python_version<'3.12'" -> "foo-bar"
   """
   s = requirement.split(";", 1)[0].strip()  # get the first section
   s = s.split("[", 1)[0].strip()            # remove optional tags
   for ch in "<>!=~":                        # remove versioning characters
      s = s.split(ch, 1)[0].strip()
   return s

def bundleTar():
   """
   Generates a tar.gz archive of a completed MacOS PEM build.
   Unpacking a tar.gz preserves execute permissions, which is necessary
   to distribute the macOS build.
   On Windows, a simple .zip is acceptable.
   """
   if system.startswith("MacOS"):
      import subprocess
      distPath = buildPath / "dist" / system

      # Ad-hoc sign the app to reduce Gatekeeper friction.
      # This prevents the "app is damaged" error but users on macOS 13+ may still
      # see a warning that the developer cannot be verified.
      #
      # NOTE: To fully bypass Gatekeeper (no warnings at all), you need an Apple
      # Developer ID ($99/year). The steps are:
      #   1. Enroll in the Apple Developer Program and create a
      #      "Developer ID Application" certificate in Xcode/Keychain.
      #   2. In generateSpecFile(), set codesign_identity to your certificate name,
      #      e.g. codesign_identity="Developer ID Application: Your Name (TEAMID)"
      #   3. After building, notarize and staple before creating the tarball:
      #        xcrun notarytool submit PEM.app --apple-id you@email.com \
      #            --team-id TEAMID --password APP_SPECIFIC_PASSWORD --wait
      #        xcrun stapler staple PEM.app
      #   Consider adding a --notarize flag to this script to gate those steps.
      appPath = distPath / f"{appName}.app"
      subprocess.check_call(["codesign", "--deep", "--force", "--sign", "-", str(appPath)])

      subprocess.check_call(
         ["tar", "-czf", f"{str(distPath)}/{appName}-{version}.tar.gz", "-C", str(distPath), f"{appName}.app"]
      )

      # cleanup: remove the uncompressed .app and COLLECT directory after archiving
      shutil.rmtree(str(appPath))
      collectPath = distPath / appName
      if collectPath.exists():
         shutil.rmtree(str(collectPath))


def bundleZip():
   """
   Generates a .zip archive of a completed Windows PEM build.
   On Windows, a .zip is acceptable (unlike MacOS, which requires tar.gz
   to preserve execute permissions).
   """
   if system.startswith("Windows"):
      import zipfile
      distPath = buildPath / "dist" / system
      exePath  = distPath / f"{appName}.exe"
      zipPath  = distPath / f"{appName}-{version}.zip"

      with zipfile.ZipFile(str(zipPath), "w", zipfile.ZIP_DEFLATED) as zf:
         zf.write(str(exePath), f"{appName}.exe")

      # cleanup: remove the unzipped executable after archiving
      exePath.unlink()


def generateSpecFile():
   """Automatically generate a PyInstaller .spec file for PEM."""
   import PyInstaller.utils.hooks as pyhooks

   global appName, system, buildPath, mainScriptPath, specPath, rootPath
   global soundfontPath
   writeSuccess = True  # flips to False when an error occurs

   binaries = []       # bundled program binaries (portaudio, etc.)
   hiddenimports = [] + CORE_LIBRARIES  # bundled python libraries
   datas    = []       # supporting data (soundfonts, etc.)
   excludes = CORE_EXCLUDES + TESTING_EXCLUDES + PYSIDE6_EXCLUDES  # libraries to explicitly exclude
   console  = False    # show terminal while running?  (turn this off if we have a GUI)

   # get all standard library modules to ensure complete inclusion
   # We add these to datas so student code running inside the PEM app can import any standard library module (e.g. wave, sqlite3), not just the ones PEM itself uses
   stdlibPath = Path(os.path.dirname(os.__file__))
   for item in stdlibPath.iterdir():
      # check each item in our PATH
      if not (item.name.lower() in ['site-packages', '__pycache__', 'tests', 'test', 'idlelib', 'turtledemo']):
         # if it's not an external library, collect it
         if item.is_dir():
            # preserve directory layout
            datas.append((str(item), f"python_lib/{item.name}"))
         else:
            # add individual library
            datas.append((str(item), "python_lib"))

   # add dependencies from pyproject.toml
   dependencies = []
   pyprojectDeps = getDependencies()
   packageToImport = {  # map known cases where package name != import name
      "python-rtmidi" : "rtmidi",
      "pyinstaller"   : "PyInstaller",
   }
   for requirement in pyprojectDeps:
      distName = getPEPName(requirement)  # get package name
      importName = packageToImport.get(distName, distName)  # convert to import name
      if importName:
         dependencies.append(importName)  # add dependency
   hiddenimports += dependencies  # import dependencies

   # add optional packages
   extraPackages = []
   for importNames in EXTRA_PACKAGES.values():
      extraPackages.extend(importNames)
   hiddenimports += extraPackages

   # add PyInstaller hooks
   hiddenimports += pyhooks.collect_submodules("PyInstaller")
   datas += pyhooks.collect_data_files("PyInstaller", include_py_files=True)

   # ensure setuptools and PythonMusic metadata is present
   datas += pyhooks.copy_metadata("setuptools")
   datas += pyhooks.copy_metadata("PythonMusic")

   # add PEM/IDLE hooks
   hookspath = [
      str(buildPath / "hook"),
   ]

   if "--include-soundfont" in sys.argv:
      # add soundfont, if it exists (we checked already in checkRequirements() - but just in case)
      if (soundfontPath is not None) and (soundfontPath.exists()):
         datas.append((str(soundfontPath), "soundfonts"))


   # define system-specific settings
   if system.startswith("MacOS"):  # MacOS
      # On MacOS, we need to use BUNDLE to create a single .app executable.

      # set icon path (Windows uses .ico, MacOS uses .icns)
      iconPath = rootPath / "src" / "pem" / "icons" / "icon.icns"
      if iconPath.exists():
         iconValue = repr(str(iconPath))
      else:
         iconValue = "None"

      # bundle portaudio
      libportaudio = rootPath / "src" / "PythonMusic" / "bin" / "libportaudio.2.dylib"
      if libportaudio.exists():
         binaries.append((str(libportaudio), "."))

      # # ensure python location is registered
      # libpython = Path(sys.exec_prefix, "lib", "libpython3.12.dylib")
      # if libpython.exists():
      #    binaries.append((str(libpython), "."))

      ### FULL APP BUILD
      exeText = f"""\
exe = EXE(
   pyz,
   a.scripts,
   [],
   exclude_binaries=True,
   name='{appName}',
   debug=False,
   bootloader_ignore_signals=False,
   strip=False,
   upx=True,
   upx_exclude=[],
   console={console},
   disable_windowed_traceback=False,
   argv_emulation=False,
   target_arch=None,
   codesign_identity=None,
   entitlements_file=None,
   icon={iconValue}
)
coll = COLLECT(
   exe,
   a.binaries,
   a.zipfiles,
   a.datas,
   strip=False,
   upx=True,
   upx_exclude=[],
   name='{appName}'
)
app = BUNDLE(
   coll,
   name='{appName}.app',
   icon={iconValue},
   bundle_identifier=None,
   info_plist={{
      "CFBundleShortVersionString": "{version}",
      "CFBundleVersion": "{version}",
      # Keep macOS's Start Dictation and Emoji & Symbols out of the Edit menu
      # (see pem.macosx._hideSystemEditMenuItems, which does the same when
      # PEM runs from source).
      "NSDisabledDictationMenuItem": True,
      "NSDisabledCharacterPaletteMenuItem": True,
   }},
)
"""
#       ### COMPRESSED BINARY BUILD (for debug only)
#       exeText = f"""\
# exe = EXE(
#    pyz,
#    a.scripts,
#    a.binaries,
#    a.zipfiles,
#    a.datas,
#    [],
#    onefile=True,
#    exclude_binaries=False,
#    name='{appName}',
#    debug=False,
#    bootloader_ignore_signals=False,
#    strip=False,
#    upx=True,
#    upx_exclude=[],
#    console={console},
#    disable_windowed_traceback=False,
#    argv_emulation=False,
#    target_arch=None,
#    codesign_identity=None,
#    entitlements_file=None,
#    icon={iconValue},
#    manifest=None
# )
# app = BUNDLE(
#    exe,
#    name='{appName}.app',
#    icon={iconValue},
#    bundle_identifier=None,
#    info_plist={{
#       "CFBundleShortVersionString": "{version}",
#       "CFBundleVersion": "{version}",
#    }},
# )
# """

   else:
      # On any other OS, we keep onefile behavior.

      # set icon path (only on Windows)
      if system.startswith("Windows"):
         iconPath = rootPath / "src" / "pem" / "icons" / "icon.ico"
         if iconPath.exists():
            iconValue = repr(str(iconPath))
         else:
            iconValue = "None"
      else:
         iconValue = "None"

      ### ONEFILE BUILD
      exeText = f"""\
exe = EXE(
   pyz,
   a.scripts,
   a.binaries,
   a.zipfiles,
   a.datas,
   [],
   exclude_binaries=False,
   name='{appName}',
   debug=False,
   bootloader_ignore_signals=False,
   strip=False,
   upx=True,
   upx_exclude=[],
   onefile=True,
   console={console},
   disable_windowed_traceback=False,
   icon={iconValue},
   manifest=None,
)
"""

#       ### ONEDIR BUILD
#       exeText = f"""\
# exe = EXE(
#    pyz,
#    a.scripts,
#    [],
#    exclude_binaries=True,
#    name='{appName}',
#    debug=False,
#    bootloader_ignore_signals=False,
#    strip=False,
#    upx=True,
#    upx_exclude=[],
#    console={console},
#    disable_windowed_traceback=False,
#    argv_emulation=False,
#    target_arch=None,
#    codesign_identity=None,
#    entitlements_file=None,
#    icon={iconValue},
#    manifest=None,
# )
# coll = COLLECT(
#    exe,
#    a.binaries,
#    a.zipfiles,
#    a.datas,
#    strip=False,
#    upx=True,
#    upx_exclude=[],
#    name='{appName}'
# )
# """

   # generate specification code to write to file
   specText = f"""\
# -*- mode: python ; coding: utf-8 -*-
# Automatically generated spec file for PEM.
# This file is regenerated whenever build.py is run.
a = Analysis(
   [{repr(str(mainScriptPath))}],
   pathex=[],
   binaries={repr(binaries)},
   datas={repr(datas)},
   hiddenimports={repr(hiddenimports)},
   hookspath={repr(hookspath)},
   hooksconfig={{}},
   runtime_hooks=[],
   excludes={repr(excludes)},
   win_no_prefer_redirects=False,
   win_private_assemblies=False,
   noarchive=False,
   optimize=0,
)
pyz = PYZ(
   a.pure,
   a.zipped_data,
)
{exeText}
"""

   # ensure the build directory exists
   specPath.parent.mkdir(parents=True, exist_ok=True)

   # now, write (or overwrite) the .spec file
   try:
      Path(specPath).write_text(specText, encoding="utf-8")
   except Exception as e:
      printd(f"Error: Failed to generate PyInstaller specifications: {e}")
      writeSuccess = False

   # verify the .spec file exists
   if writeSuccess and not specPath.exists():
      writeSuccess = False

   return writeSuccess


if __name__ == "__main__":
   # Propagate the build's exit code to the process so callers (and CI) can
   # tell a failed build from a successful one.
   sys.exit(main())
