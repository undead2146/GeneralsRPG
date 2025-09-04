# -*- coding: utf-8 -*-
"""
Item + crafting system for GeneralsRPG.
"""

from typing import Dict, Any


class Item:
    def __init__(self, name: str, rarity: str, owned: int = 1, **kwargs):
        self.name = name
        self.rarity = rarity
        self.owned = owned
        self.meta = kwargs

    def __str__(self):
        return f"{self.name} ({self.rarity})"


async def craft_from_blueprint(ctx, character, item_name: str) -> (bool, str):
    """Consume materials to craft an item."""
    bp = character.backpack.get(item_name)
    if not bp or bp.owned <= 0:
        return False, f"No blueprint for {item_name}."
    # Example: consume 1 blueprint + 2 parts
    if character.backpack.get("Parts", 0) < 2:
        return False, "Not enough Parts."
    character.backpack[item_name].owned -= 1
    character.backpack["Parts"] -= 2
    return True, f"Successfully crafted {item_name}!"
