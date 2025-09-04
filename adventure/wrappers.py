"""Compatibility shim re-exporting the wrapper commands.

The implementation moved to :mod:`adventure.commands.wrappers`. Keep this shim
so third-party imports of ``adventure.wrappers`` continue to work during the
refactor.

"""

try:
	from adventure.core.wrappers import *  # noqa: F401,F403
	__all__ = [name for name in globals().keys() if not name.startswith("_")]
except Exception:  # pragma: no cover - fallback for minimal environments
	try:
		from adventure.commands.wrappers import *  # noqa: F401,F403
	except Exception:
		# if command-layer wrapper isn't available, provide a minimal shim
		class WrapperCommands:
			pass

	__all__ = [name for name in globals().keys() if not name.startswith("_")]
