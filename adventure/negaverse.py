"""Compatibility shim: `adventure.negaverse` moved to `adventure.commands.negaverse`.

Keep a thin shim so existing imports that reference `adventure.negaverse`
continue to work while the codebase migrates.
"""

try:
	from adventure.core.negaverse import *  # noqa: F401,F403
	__all__ = [name for name in globals().keys() if not name.startswith("_")]
except Exception:  # pragma: no cover - fallback for environments without core
	from adventure.commands.negaverse import *  # noqa: F401,F403
	__all__ = ["Negaverse"]
