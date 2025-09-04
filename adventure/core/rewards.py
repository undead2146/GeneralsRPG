# -*- coding: utf-8 -*-
"""
RewardEngine for GeneralsRPG.

Handles:
- XP / CP distribution
- Supplies, Parts, Blueprints
- Treasure chest rolls
"""

import random
from typing import Any, Dict, List, Optional

from .constants import Treasure


class RewardEngine:
    def __init__(self, config: Dict[str, Any], seed: Optional[int] = None):
        self.config = config or {}
        self.rng = random.Random(seed)

    def calculate(
        self,
        context: str,
        participants: List[Dict[str, Any]],
        outcome: Optional[Any] = None,
    ) -> Dict[int, Dict[str, Any]]:
        """
        Compute rewards for participants.

        Returns:
            reward_map: {user_id: {"xp": int, "cp": int, "supplies": int, ...}}
        """
        reward_map: Dict[int, Dict[str, Any]] = {}
        for p in participants:
            uid = p["id"]
            reward_map[uid] = {
                "xp": self.rng.randint(50, 150),
                "cp": self.rng.randint(20, 80),
                "supplies": self.rng.randint(0, 5),
                "parts": self.rng.randint(0, 2),
                "blueprints": 1 if self.rng.random() < 0.05 else 0,
            }
        return reward_map


def roll_treasure(rng: random.Random, difficulty: int = 1) -> Treasure:
    """Roll a treasure chest reward based on difficulty."""
    if difficulty > 5:
        return Treasure(epic=1, legendary=1)
    elif difficulty > 2:
        return Treasure(rare=1)
    return Treasure(normal=1)
