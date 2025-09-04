"""Backwards-compat shim for `adventure.leaderboards`.

The implementation has moved to `adventure.commands.leaderboards`. Importing
this module re-exports from the new location so third-party code and tests
that import `adventure.leaderboards` continue to work during the
incremental refactor.
"""

try:
	from adventure.core.leaderboards import *  # noqa: F401,F403
	__all__ = [name for name in globals().keys() if not name.startswith("_")]
except Exception:  # pragma: no cover - fallback for environments without core
	from adventure.commands.leaderboards import *  # noqa: F401,F403
	__all__ = ["LeaderboardCommands"]
