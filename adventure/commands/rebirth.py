# -*- coding: utf-8 -*-
"""
Rebirth command mixin for GeneralsRPG.
Delegates to core.character for rebirth logic.
"""

import time
from redbot.core import commands
from redbot.core.i18n import Translator
from adventure.core.character import Character
from adventure.core.economy import remove_cp
from adventure.ui.helpers import smart_embed

_ = Translator("Adventure", __file__)


class RebirthCommands:
    @commands.hybrid_command(name="rebirth")
    @commands.guild_only()
    async def rebirth(self, ctx: commands.Context):
        """Reset your character to level 1 and gain a rebirth."""
        if self.in_adventure(ctx):
            return await smart_embed(ctx, _("You cannot rebirth during an adventure."))

        async with self.get_lock(ctx.author):
            c = await Character.from_json(ctx, self.config, ctx.author, self._daily_bonus)
            if c.lvl < c.data.get("maxlevel", 20):
                return await smart_embed(ctx, _("You must reach max level to rebirth."))

            cost = 1000 * (c.rebirths + 1)
            if c.bal < cost:
                return await smart_embed(
                    ctx,
                    _("You need {cost} credits to rebirth.").format(cost=cost),
                )

            await remove_cp(ctx.author, cost)
            await self.config.user(ctx.author).set(await c.rebirth())
            return await smart_embed(
                ctx,
                _("Congratulations {user}, you have rebirthed!").format(user=ctx.author.display_name),
                success=True,
            )
