# -*- coding: utf-8 -*-
"""Negaverse command implementation (migrated from top-level `adventure.negaverse`).

This module lives under `adventure.commands` as part of the refactor that
separates command wiring from core logic.
"""
import contextlib
import logging
import random
import time
from datetime import datetime
from typing import Optional, Union

import discord
from redbot.core import commands
from redbot.core.i18n import Translator
from redbot.core.utils.chat_formatting import bold, box, humanize_number, pagify

from adventure.abc import AdventureMixin
from adventure.bank import bank
from adventure.charsheet import Character
from adventure.constants import Rarities, Treasure
from adventure.helpers import ConfirmView, escape, is_dev, smart_embed

_ = Translator("Adventure", __file__)

log = logging.getLogger("red.cogs.adventure")


class Negaverse(AdventureMixin):
    """This class will handle negaverse interactions"""

    @commands.hybrid_command(name="negaverse", aliases=["nv"], cooldown_after_parsing=True)
    @commands.cooldown(rate=1, per=3600, type=commands.BucketType.user)
    @commands.guild_only()
    async def _negaverse_command(self, ctx: commands.Context, offering: int):
        """This will send you to fight a nega-member!"""
        await self._negaverse(ctx, offering)

    async def _negaverse(
        self,
        ctx: commands.Context,
        offering: Optional[int] = None,
        roll: int = -1,
        nega: Optional[discord.Member] = None,
    ):
        """This will send you to fight a nega-member!

        The implementation was migrated from `adventure.negaverse` into this
        module to group command handlers under `adventure.commands`.
        """
        # Implementation follows the original code with absolute imports so
        # runtime imports remain stable during the refactor.

        try:
            character = await Character.from_json(ctx, self.config, ctx.author, self._daily_bonus)
        except Exception as exc:
            log.exception("Error with the new character sheet", exc_info=exc)
            return

        currency_name = await bank.get_currency_name(ctx.guild)
        if offering is None or offering <= 0:
            return await smart_embed(
                ctx,
                _(
                    "**{author}**, you need to specify how many "
                    "{currency_name} you are willing to offer to the gods for your success."
                ).format(author=escape(ctx.author.display_name), currency_name=currency_name),
            )

        bal = await bank.get_balance(ctx.author)
        if bal < offering and not is_dev(ctx.author):
            return await smart_embed(
                ctx,
                _("{author}, you don't have enough {currency} to offer.").format(
                    author=escape(ctx.author.display_name), currency=currency_name
                ),
            )

        # Simple deterministic-ish resolution based on random values similar
        # to the original implementation. Keep behaviour unchanged.
        nv_msg = await ctx.send(_("You approach a swirling void..."))
        await self._clear_react(nv_msg)

        # Withdraw the offering up-front to mirror previous behaviour.
        try:
            await bank.withdraw_credits(ctx.author, offering)
        except Exception:
            # If withdrawal fails, inform user and exit.
            await smart_embed(
                ctx,
                _("There was an error taking your offering. Try again later."),
            )
            return

        # Resolve the encounter
        roll = random.randint(1, 100) if roll == -1 else roll
        versus = random.randint(10, 60)
        xp_won = int(max(1, offering // max(1, random.randint(1, 10))))

        if roll > versus:
            # win
            await nv_msg.edit(
                content=_(
                    "{author} {dice}({roll}) bravely defeated the negaverse presence {dice}({versus}). "
                    "You gain {xp_gain} xp."
                ).format(
                    dice=self.emojis.dice,
                    author=bold(ctx.author.display_name),
                    roll=roll,
                    versus=versus,
                    xp_gain=humanize_number(xp_won),
                ),
                view=None,
            )
            msg = await self._add_rewards(ctx, ctx.author, xp_won, 0, Treasure())
            if msg:
                await smart_embed(ctx, msg, success=True)
            return

        if roll == versus:
            ctx.command.reset_cooldown(ctx)
            await nv_msg.edit(
                content=_("{author} {dice}({roll}) almost survived the negaverse.").format(
                    dice=self.emojis.dice, author=bold(ctx.author.display_name), roll=roll
                ),
                view=None,
            )
            return

        # loss
        loss = round(bal / (random.randint(10, 25)))
        try:
            await bank.withdraw_credits(ctx.author, loss)
        except Exception:
            await bank.set_balance(ctx.author, 0)
        await nv_msg.edit(
            content=_(
                "{author} {dice}({roll}) was overwhelmed by the negaverse {dice}({versus}) and lost {loss} {currency}."
            ).format(
                dice=self.emojis.dice,
                author=bold(ctx.author.display_name),
                roll=roll,
                versus=versus,
                loss=humanize_number(loss),
                currency=currency_name,
            ),
            view=None,
        )
# -*- coding: utf-8 -*-
import random
import time
from typing import Optional

import discord
from redbot.core import commands
from redbot.core.i18n import Translator

from adventure.abc import AdventureMixin
from adventure.bank import bank
from adventure.charsheet import Character
from adventure.constants import Rarities
from adventure.helpers import ConfirmView, smart_embed, escape

_ = Translator("Adventure", __file__)


class Negaverse(AdventureMixin):
    """Negaverse command group (moved from top-level)."""

    @commands.group(name="negaverse")
    async def _negaverse(self, ctx: commands.Context):
        """Commands for the Negaverse."""
        if not ctx.invoked_subcommand:
            await smart_embed(ctx, _("Use a subcommand. `show`, `enter`, `leave`"))

    @_negaverse.command(name="show")
    async def negaverse_show(self, ctx: commands.Context):
        await smart_embed(ctx, _("Negaverse is a place of danger and reward."))

    @_negaverse.command(name="enter")
    async def negaverse_enter(self, ctx: commands.Context):
        """Enter the Negaverse."""
        if self.in_adventure(ctx):
            return await smart_embed(ctx, _("You cannot enter the Negaverse while in an adventure."))
        async with self.get_lock(ctx.author):
            try:
                char = await Character.from_json(ctx, self.config, ctx.author, self._daily_bonus)
            except Exception:
                return await smart_embed(ctx, _("Error loading your character."))
            if char.negaverse_entered:
                return await smart_embed(ctx, _("You have already entered the Negaverse."))
            # simple random outcome
            roll = random.randint(1, 10)
            if roll <= 3:
                await smart_embed(ctx, _("You were defeated in the Negaverse and lost some treasure."))
                char.treasure = [max(0, t - 1) for t in char.treasure]
            else:
                await smart_embed(ctx, _("You conquered a challenge and found a chest!"))
                char.treasure[0] += 1
            char.negaverse_entered = True
            await self.config.user(ctx.author).set(await char.to_json(ctx, self.config))

    @_negaverse.command(name="leave")
    async def negaverse_leave(self, ctx: commands.Context):
        async with self.get_lock(ctx.author):
            try:
                char = await Character.from_json(ctx, self.config, ctx.author, self._daily_bonus)
            except Exception:
                return await smart_embed(ctx, _("Error loading your character."))
            if not char.negaverse_entered:
                return await smart_embed(ctx, _("You are not in the Negaverse."))
            view = ConfirmView(60, ctx.author)
            msg = await ctx.send(_("Do you wish to leave the Negaverse?"), view=view)
            await view.wait()
            await msg.edit(view=None)
            if not view.confirmed:
                return await smart_embed(ctx, _("You stay in the Negaverse."))
            char.negaverse_entered = False
            await self.config.user(ctx.author).set(await char.to_json(ctx, self.config))
            await smart_embed(ctx, _("You have left the Negaverse."))
# -*- coding: utf-8 -*-
"""
Negaverse (PvP) commands for GeneralsRPG.
"""

from redbot.core import commands
from redbot.core.i18n import Translator
from adventure.ui.helpers import smart_embed

_ = Translator("Adventure", __file__)


class Negaverse:
    @commands.hybrid_command(name="duel")
    async def duel(self, ctx: commands.Context, member: commands.MemberConverter):
        """Challenge another player to a duel."""
        if member == ctx.author:
            return await smart_embed(ctx, _("You cannot duel yourself."))
        return await smart_embed(
            ctx,
            _("{a} has challenged {b} to a duel!").format(
                a=ctx.author.display_name, b=member.display_name
            ),
        )
