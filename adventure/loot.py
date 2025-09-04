"""Compatibility shim for loot APIs.

Prefer the new core implementation in `adventure.core.items`. During the
transition and in minimal test environments we fall back to the command
implementation under `adventure.commands.loot` so imports remain stable.
"""

try:
    # canonical implementation
    from adventure.core.items import Item, craft_from_blueprint
    __all__ = ["Item", "craft_from_blueprint"]
except Exception:
    # fallback compatibility shim
    from adventure.commands.loot import *  # noqa: F401,F403
    __all__ = ["LootCommands", "craft_from_blueprint"]
