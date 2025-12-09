"""Input Monitor package

This package exposes a simple API and a command line entry point.
"""

from .version import VERSION as __version__  # reexport for consumers
from . import app as app  # re-export the app module for convenience

__all__ = ["__version__", "app"]
