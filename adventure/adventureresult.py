"""Compatibility shim re-exporting adventureresult moved into core.

The implementation now lives in :mod:`adventure.core.adventureresult`.
Keeping this small shim preserves backward-compatible imports that
target :mod:`adventure.adventureresult`.
"""

from adventure.core.adventureresult import *  # noqa: F401,F403

__all__ = ["StatRange", "AdventureResults"]
