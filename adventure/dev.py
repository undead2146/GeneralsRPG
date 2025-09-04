"""Compatibility shim re-exporting the developer commands.

The real implementation lives in adventure.commands.dev after the refactor.
"""

try:
	from adventure.core.dev import *  # noqa: F401,F403
	__all__ = [name for name in globals().keys() if not name.startswith("_")]
except Exception:  # pragma: no cover - fallback for environments without core
	from adventure.commands.dev import *  # noqa: F401,F403
	__all__ = ["DevCommands"]
