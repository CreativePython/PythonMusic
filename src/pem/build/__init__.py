"""Build configuration shared by PEM's own PyInstaller build and the editor's
"Create Executable" feature.

This lives inside the shipped ``pem`` package (rather than the ``PEM/`` build
folder) so that a pip-installed or frozen PEM can still read the same package
lists and exclusions when a student builds an executable from their script.
"""
