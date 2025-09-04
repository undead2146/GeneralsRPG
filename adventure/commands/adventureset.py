"""Compatibility shim for `adventure.commands.adventureset`.

Provide a minimal, import-time-safe `AdventureSetCommands` mixin so
modules that import `adventure.commands.adventureset` can proceed during
tests without triggering a circular import. The real implementation
remains under `adventure.adventureset` and can replace this shim later.
"""

from typing import Any


class AdventureSetCommands:
	"""Minimal mixin placeholder for the AdventureSet commands.

	This class intentionally implements no behaviour; it exists only
	to satisfy imports and class hierarchies during tests.
	"""

	def __init__(self, *args: Any, **kwargs: Any):
		# deliberately minimal to be import-time safe
		super().__init__()


__all__ = ["AdventureSetCommands"]
