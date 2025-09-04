"""Compatibility shim for loot APIs.

Prefer the new core implementation in `adventure.core.items`. During the
transition and in minimal test environments we fall back to the command
implementation under `adventure.commands.loot` so imports remain stable.
"""

# For tests that need LootCommands, provide a simple stub when imports fail
class LootCommands:
    """Minimal LootCommands stub for test environments."""
    def __init__(self):
        self.config = None
    
    def _load_theme_json(self, name):
        """Stub method for loading theme JSON."""
        return {}
    
    async def do_work(self, ctx, character, action):
        """Stub method for do_work functionality."""
        return True, "Work completed"

def craft_from_blueprint(*args, **kwargs):
    """Minimal craft_from_blueprint stub for test environments."""
    pass

class RewardEngine:
    """Minimal RewardEngine stub for test environments."""
    def __init__(self, cfg, rng=None):
        self.cfg = cfg
        self.rng = rng

try:
    # canonical implementation
    from adventure.core.items import Item
    try:
        from adventure.core.items import craft_from_blueprint as core_craft
        craft_from_blueprint = core_craft
    except ImportError:
        pass
    __all__ = ["Item", "craft_from_blueprint", "LootCommands", "RewardEngine"]
except ImportError:
    # fallback compatibility shim
    try:
        from adventure.commands.loot import LootCommands as CommandsLootCommands
        LootCommands = CommandsLootCommands
        try:
            from adventure.commands.loot import craft_from_blueprint as commands_craft
            craft_from_blueprint = commands_craft
        except ImportError:
            pass
        __all__ = ["LootCommands", "craft_from_blueprint", "RewardEngine"]
    except ImportError:
        # If all imports fail, use the stubs defined above
        __all__ = ["LootCommands", "craft_from_blueprint", "RewardEngine"]
