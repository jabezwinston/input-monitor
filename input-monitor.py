"""Run `input_monitor` package as a script using the hyphenated filename.

Note: Running `python3 -m input-monitor` is not supported because hyphens
are not valid module names for `-m`. Use one of the following instead:

  - `python3 -m input_monitor` (underscore form)
  - `python3 input-monitor.py` (this script)
  - `./input-monitor` (executable wrapper script included)

This file simply forwards to the package entry point.
"""

from input_monitor.app import main


if __name__ == "__main__":
    main()
