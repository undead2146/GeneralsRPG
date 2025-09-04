# -*- coding: utf-8 -*-
"""
Character model for GeneralsRPG.

Handles:
- Persistent stats (att, int, cha, rebirths, etc.)
- Inventory (backpack, units, builders)
- Serialization to/from JSON
"""

import time
from typing import Any, Dict


class Character:
    def __init__(self, user_id: int, data: Dict[str, Any]):
        self.id = user_id
        self.data = data or {}
        self.lvl = self.data.get("lvl", 1)
        self.rebirths = self.data.get("rebirths", 0)
        self.bal = self.data.get("bal", 0)
        self.backpack = self.data.get("backpack", {})
        self.units = self.data.get("units", {})
        self.builders = self.data.get("builders", {})
        self.last_currency_check = self.data.get("last_currency_check", int(time.time()))

    @classmethod
    async def from_json(cls, ctx, config, user, daily_bonus):
        """Load character from config storage."""
        data = await config.user(user).all()
        return cls(user.id, data)

    async def to_json(self, ctx, config) -> Dict[str, Any]:
        """Serialize character back to config."""
        return {
            "lvl": self.lvl,
            "rebirths": self.rebirths,
            "bal": self.bal,
            "backpack": self.backpack,
            "units": self.units,
            "builders": self.builders,
            "last_currency_check": self.last_currency_check,
        }

    async def rebirth(self):
        """Reset level, increment rebirths."""
        self.lvl = 1
        self.rebirths += 1
        return await self.to_json(None, None)
