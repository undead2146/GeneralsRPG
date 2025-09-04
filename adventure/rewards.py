"""Shim for `adventure.rewards` that re-exports implementation from
`adventure.core.rewards` during refactor.
"""

from adventure.core.rewards import *  # noqa: F401,F403

__all__ = ['RewardEngine']

