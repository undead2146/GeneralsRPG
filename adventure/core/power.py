# -*- coding: utf-8 -*-
"""
Power-related game logic moved into core during refactor. This file mirrors the
original `adventure/power.py` implementation so that behavior remains unchanged
while we reorganize the package layout.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

from redbot.core import commands
from redbot.core.i18n import Translator

from adventure.charsheet import Character
from adventure.helpers import smart_embed

_ = Translator("Adventure", __file__)

log = logging.getLogger("red.cogs.adventure")


@dataclass
class Power:
    name: str
    cost: int
    description: str


class PowerCommands(commands.Cog):
    """Cog providing power-related commands for characters."""

    def __init__(self, bot):
        self.bot = bot
        self.powers: Dict[str, Power] = {}

    def add_power(self, name: str, cost: int, description: str):
        self.powers[name] = Power(name, cost, description)

    @commands.command(name="powers")
    async def list_powers(self, ctx: commands.Context):
        """List all available powers."""
        lines: List[str] = []
        for p in sorted(self.powers.values(), key=lambda x: x.name):
            lines.append(f"{p.name}: {p.cost} - {p.description}")
        await smart_embed(ctx, "\n".join(lines) or _("No powers available."))

    @commands.command(name="usepower")
    async def use_power(self, ctx: commands.Context, name: str):
        """Use a named power if the character has enough resources."""
        try:
            c = await Character.from_json(ctx, None, ctx.author, 0)
        except Exception as exc:
            log.exception("Error loading character", exc_info=exc)
            await smart_embed(ctx, _("Error loading your character."))
            return
        power = self.powers.get(name)
        if not power:
            await smart_embed(ctx, _("That power does not exist."))
            return
        if c.bal < power.cost:
            await smart_embed(ctx, _("You do not have enough funds to use that power."))
            return
        await smart_embed(ctx, _("You used {name}!").format(name=power.name))
