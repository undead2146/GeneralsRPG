"""Power related commands moved to commands package.

This module re-exports the core implementation for commands that are thin
and Discord-specific while keeping the logic in `adventure.core.power`.
"""
from adventure.core.power import *  # noqa: F401,F403

__all__ = ["Power", "PowerCommands"]
# -*- coding: utf-8 -*-
"""
Power commands for GeneralsRPG.
"""

from redbot.core import commands
from redbot.core.i18n import Translator
from adventure.ui.helpers import smart_embed

_ = Translator("Adventure", __file__)


class PowerCommands:
    @commands.hybrid_command(name="powers")
    async def powers(self, ctx: commands.Context):
        """List available powers."""
        # TODO: fetch from config or core
        return await smart_embed(ctx, _("Available powers: Airstrike, Repair, Supply Drop"))
