# Input Monitor

A small Tkinter widget that displays keyboard and mouse events (input monitor).

Run it from source (dev mode):

```bash
python -m input_monitor
# or after installing in editable mode
pip install -e .
input-monitor
```

Packaging
```
python -m build
pip install dist/input-monitor-<version>.tar.gz
```

Dynamic versioning

This package uses a dynamic version (see `pyproject.toml`) and reads the value from `input_monitor.version.VERSION` at build time. Update `input_monitor/version.py` or set VERSION via CI prior to building releases.
