"""Compatibility shim re-exporting backpack command group.

The implementation has been moved to :mod:`adventure.commands.backpack`.
Keep this shim so existing imports of :mod:`adventure.backpack` continue
to work during the refactor.
"""

try:
	from adventure.core.backpack import BackPackCommands  # type: ignore
	__all__ = ["BackPackCommands"]
except Exception:  # pragma: no cover - fallback for minimal environments
	from adventure.commands.backpack import *  # noqa: F401,F403
	__all__ = [
		"BackPackCommands",
		"BackpackSellView",
		"BackpackMenu",
	]
