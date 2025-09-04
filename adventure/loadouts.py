"""Backwards-compat shim for `adventure.loadouts`.

The implementation has moved to `adventure.commands.loadouts`. Importing
this module re-exports from the new location so third-party code and tests
that import `adventure.loadouts` continue to work during the
incremental refactor.
"""

try:
	from adventure.core.loadouts import *  # noqa: F401,F403
	__all__ = [name for name in globals().keys() if not name.startswith("_")]
except Exception:  # pragma: no cover - fallback for environments without core
	from adventure.commands.loadouts import *  # noqa: F401,F403
	__all__ = ["LoadoutCommands"]
