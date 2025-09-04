"""Small, import-time safe implementation of adventureresult helpers.

This module provides a lightweight replacement for the original
`adventure.adventureresult` during the repository reorganization so
imports used by the Adventure cog remain stable in tests.

It intentionally implements a minimal API: a `StatRange` dataclass and
an `AdventureResults` class with `get_stat_range` and `add_result`.
The real implementation can replace this later; these are focused on
being safe during import and adequate for unit tests that don't rely
on the full behaviour.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class StatRange:
	"""Simple container for stat range information."""

	min_stat: int = 0
	max_stat: int = 0


class AdventureResults:
	"""Minimal results tracker used by the Adventure cog in tests.

	This stores lightweight per-guild placeholders and supports the
	small subset of methods used during collection and in unit tests.
	"""

	def __init__(self, limit: int = 20):
		self.limit = limit
		# store a mapping guild_id -> StatRange
		self._ranges: Dict[Optional[int], StatRange] = {}

	def get_stat_range(self, guild: Any) -> StatRange:
		"""Return a StatRange for the given guild (or a default).

		Guild may be an object with an `id` attribute or a raw id.
		"""
		gid = getattr(guild, "id", guild)
		if gid not in self._ranges:
			self._ranges[gid] = StatRange(min_stat=0, max_stat=0)
		return self._ranges[gid]

	def add_result(self, guild: Any, action: str, value: int, people: int, flag: bool) -> None:
		"""Record a result for the given guild.

		The implementation is intentionally minimal: it ensures a StatRange
		exists and does not perform complex aggregation. This is sufficient
		for tests that only verify call sites and the presence of the API.
		"""
		gid = getattr(guild, "id", guild)
		self._ranges.setdefault(gid, StatRange())
		# no-op beyond ensuring presence
		return

