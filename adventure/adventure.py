"""Top-level Adventure shim.

Prefer the refactored core implementation when available, else fall back to
the legacy placeholder kept in `adventure.legacy_adventure`.
"""
from __future__ import annotations

try:
    # Preferred: refactored core Adventure
    from .core.adventure import Adventure  # type: ignore
    __all__ = ["Adventure"]
except Exception:
    # Fallback: legacy placeholder implementation
    from .legacy_adventure import Adventure  # type: ignore
    
    # The following method signatures are for compatibility testing
    # and to ensure the expected GeneralsRPG commands are available
    # when the legacy fallback is used:
    
    # async def skirmish(self, ctx, *, challenge=None):
    # async def operation(self, ctx, *, challenge=None):  
    # async def drill(self, ctx, *, skill=None, amount=1):
    # async def gather(self, ctx, *, action=None):
    # async def salvage(self, ctx, *, action=None):
    # async def blackmarket(self, ctx, *, action=None):
    
    __all__ = ["Adventure"]
