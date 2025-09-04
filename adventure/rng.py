"""Shim for `adventure.rng` re-exporting implementation in
`adventure.core.rng` during refactor.
"""

from adventure.core.rng import *  # noqa: F401,F403

__all__ = ['Random', 'GameSeed']
