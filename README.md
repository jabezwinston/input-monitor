# Input Monitor

A small Tkinter widget that displays keyboard and mouse events (input monitor).

Run it from source (dev mode):

```bash
# Run as a module (note: module names cannot contain hyphens, so use the underscore package name)
python -m input_monitor
# or after installing in editable mode, use the console script named with the hyphen
pip install -e .
input-monitor
```

Note: `python -m input-monitor` is not supported because Python module names must be valid identifiers (hyphens are not allowed). Use `input-monitor` from the command line (console script), or run as a module with the underscore version `python -m input_monitor`.

Packaging
```
python -m build
pip install dist/input-monitor-<version>.tar.gz
```
