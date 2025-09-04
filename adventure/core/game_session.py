# -*- coding: utf-8 -*-
"""
GameSession for GeneralsRPG.

Tracks:
- Current challenge (monster, boss, miniboss)
- Participants (fight, magic, talk, pray, run)
- RNG seed
- Start time
"""

import time
from typing import Dict, List, Optional

from .rng import Random


class GameSession:
    def __init__(self, ctx, cog, challenge: str, rng: Random, **kwargs):
        self.ctx = ctx
        self.cog = cog
        self.challenge = challenge
        self.rng = rng
        self.start_time = time.time()
        self.finished = False

        # Participants
        self.fight: List = []
        self.magic: List = []
        self.talk: List = []
        self.pray: List = []
        self.run: List = []

        # Monster info
        self.monster = kwargs.get("monster")
        self.monsters = kwargs.get("monsters")
        self.monster_stats = kwargs.get("monster_stats", 1.0)

    def in_adventure(self, user) -> bool:
        """Check if user is in this session."""
        return any(
            user in group for group in (self.fight, self.magic, self.talk, self.pray, self.run)
        )

    def monster_hp(self) -> Optional[int]:
        if self.monster:
            return int(self.monster.get("hp", 0) * self.monster_stats)
        return None

    def monster_dipl(self) -> Optional[int]:
        if self.monster:
            return int(self.monster.get("dipl", 0) * self.monster_stats)
        return None
