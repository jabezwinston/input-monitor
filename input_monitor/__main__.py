# Package CLI entry for `python -m input_monitor`.

try:
    from .app import main
except Exception:
    from input_monitor.app import main

if __name__ == "__main__":
    main()
