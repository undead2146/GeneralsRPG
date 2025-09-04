"""Compatibility shim re-exporting core type-hinting mixin.

The original implementation was in :mod:`adventure.abc`. During the refactor
it moved into :mod:`adventure.core.abc`. Keep this module as a thin shim so
existing imports continue to work.
"""

from adventure.core.abc import *  # noqa: F401,F403

__all__ = ["AdventureMixin"]
