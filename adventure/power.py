"""Compatibility shim re-exporting core power implementation.

During the refactor the power-related implementation moved to
``adventure.core.power`` and command wiring to ``adventure.commands.power``.
Keep this module as a thin shim so existing imports continue to work.
"""

from adventure.core.power import *  # noqa: F401,F403

__all__ = ["Power", "PowerCommands"]
