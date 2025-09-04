"""Shim module for backwards compatibility during refactor.

Local code should import types from `adventure.core.types` going forward.
This shim keeps existing imports working while we migrate files.
"""

from adventure.core.types import *  # noqa: F401,F403

__all__ = [
    'MiniBoss',
    'Monster',
]
