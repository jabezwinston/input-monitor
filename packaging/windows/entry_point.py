"""
Compatibility entry-point wrapper for PyInstaller and other packagers.

PyInstaller runs the script as __main__ (executed file), which makes relative
imports fail. Use a small wrapper that imports the package via absolute import
and launches it, so PyInstaller has a stable entry point.
"""
from input_monitor.app import main

if __name__ == "__main__":
    main()
