"""Thin wrapper commands for GeneralsRPG mapped from `adventure/adventure.py`.

This module defines a mixin-style class that contains only the lightweight
command wrappers. It is intended to be mixed into the primary Adventure cog
so the main file can be smaller and the wrappers are easier to maintain.

The wrappers preserve the original behaviour: they delegate to existing
handlers (e.g. _adventure, gather_action, salvage_action, blackmarket_action,
craft_from_blueprint, etc.) and keep the same decorators and cooldowns.
"""

from typing import Optional
import discord

try:
    from redbot.core import commands
    from redbot.core.i18n import Translator
except Exception:  # pragma: no cover - runtime/test-time fallback
    # Minimal, no-op replacements so the module can be imported during static
    # analysis or testing outside of a Red environment.
    class _NoopDecorator:
        def __init__(self, *a, **k):
            pass

        def __call__(self, func):
            return func

    class _NoopCommands:
        class BucketType:
            guild = object()
            user = object()

        hybrid_command = _NoopDecorator
        cooldown = _NoopDecorator
        bot_has_permissions = _NoopDecorator
        guild_only = _NoopDecorator

    commands = _NoopCommands()

    def Translator(name, file):
        return lambda s: s

_ = Translator("Adventure", __file__)

from ..converters import ChallengeConverter, SkillConverter
from ..charsheet import Character
from ..helpers import smart_embed
# Prefer the core implementation for crafting to avoid command->command import chains.
# This keeps the command wrapper thin and delegates the logic to adventure.core.
try:
    from adventure.core.items import craft_from_blueprint
except Exception:
    # Fallback to the command-layer implementation if core isn't available during transition/tests
    from ..loot import craft_from_blueprint


class WrapperCommands:
    """Mixin with thin wrapper commands for Adventure.

    This mixin contains only thin delegators so feature logic can live in other
    modules and the main `adventure.py` file stays focused.
    """


    @commands.hybrid_command(name="skirmish")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.guild)
    @commands.bot_has_permissions(add_reactions=True)
    @commands.guild_only()
    async def skirmish(self, ctx: "commands.Context", *, challenge: Optional[ChallengeConverter] = None):
        """Alias for adventure: short, fast engagements (GeneralsRPG style)."""
        return await self._adventure(ctx, challenge=challenge)

    @commands.hybrid_command(name="operation")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.guild)
    @commands.bot_has_permissions(add_reactions=True)
    @commands.guild_only()
    async def operation(self, ctx: "commands.Context", *, challenge: Optional[ChallengeConverter] = None):
        """Alias for adventure: harder/more intense operations (GeneralsRPG style)."""
        return await self._adventure(ctx, challenge=challenge)

    @commands.hybrid_command(name="drill")
    @commands.cooldown(rate=1, per=2, type=commands.BucketType.user)
    async def drill(self, ctx: "commands.Context", skill: Optional[SkillConverter] = None, amount: int = 1):
        """Alias for skill/training (GeneralsRPG style)."""
        return await self.skill(ctx, skill=skill, amount=amount)

    @commands.hybrid_command(name="gather")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.guild)
    @commands.bot_has_permissions(add_reactions=True)
    @commands.guild_only()
    async def gather(self, ctx: "commands.Context", *, area: Optional[ChallengeConverter] = None):
        """Gather supplies and materials from nearby zones (GeneralsRPG)."""
        try:
            return await self.gather_action(ctx, area=area)
        except Exception:
            return await self._adventure(ctx, challenge=area)

    @commands.hybrid_command(name="salvage")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.guild)
    @commands.bot_has_permissions(add_reactions=True)
    @commands.guild_only()
    async def salvage(self, ctx: "commands.Context", *, wreck: Optional[ChallengeConverter] = None):
        """Salvage parts from destroyed vehicles (GeneralsRPG)."""
        try:
            return await self.salvage_action(ctx, wreck=wreck)
        except Exception:
            return await self._adventure(ctx, challenge=wreck)

    @commands.hybrid_command(name="blackmarket")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.guild)
    @commands.bot_has_permissions(add_reactions=True)
    @commands.guild_only()
    async def blackmarket(self, ctx: "commands.Context", *, deal: Optional[ChallengeConverter] = None):
        """Attempt a black market run; high risk, high reward (GeneralsRPG)."""
        try:
            return await self.blackmarket_action(ctx, deal=deal)
        except Exception:
            return await self._adventure(ctx, challenge=deal)

    @commands.hybrid_command(name="stronghold")
    @commands.cooldown(rate=1, per=43200, type=commands.BucketType.guild)
    @commands.bot_has_permissions(add_reactions=True)
    @commands.guild_only()
    async def stronghold(self, ctx: "commands.Context", *, challenge: Optional[ChallengeConverter] = None):
        """Alias for long operations/stronghold assaults (12h shared cooldown)."""
        return await self.operation(ctx, challenge=challenge)

    @commands.hybrid_command(name="general")
    @commands.cooldown(rate=1, per=43200, type=commands.BucketType.guild)
    @commands.bot_has_permissions(add_reactions=True)
    @commands.guild_only()
    async def general(self, ctx: "commands.Context", *, challenge: Optional[ChallengeConverter] = None):
        """Alias for miniboss/general encounters (12h shared cooldown)."""
        return await self.operation(ctx, challenge=challenge)

    @commands.hybrid_command(name="blueprints")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def blueprints(self, ctx: "commands.Context"):
        """Show available blueprints / craftable tech."""
        if hasattr(self, "forge"):
            try:
                return await self.forge(ctx)
            except Exception:
                pass
        try:
            c = await Character.from_json(ctx, self.config, ctx.author, self._daily_bonus)
            items = [n for n, i in c.backpack.items() if getattr(i, "rarity", "") in ("event", "normal")]
            if not items:
                return await smart_embed(ctx, _("No blueprints or craftable tech found in your inventory."))
            return await smart_embed(ctx, _("Available blueprints: {items}").format(items=", ".join(items)))
        except Exception:
            return await smart_embed(ctx, _("Unable to retrieve blueprints at this time."))

    @commands.hybrid_command(name="build")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def build(self, ctx: "commands.Context", *, item_name: Optional[str] = None):
        """Consume materials to build a unit/upgrade. Uses existing forge/craft behaviour if present."""
        if not item_name:
            return await smart_embed(ctx, _("Please specify what you want to build."))
        if hasattr(self, "forge"):
            try:
                return await self.forge(ctx)
            except Exception:
                pass
        try:
            c = await Character.from_json(ctx, self.config, ctx.author, self._daily_bonus)
        except Exception:
            return await smart_embed(ctx, _("Could not load your character data."))

        success, msg = await craft_from_blueprint(ctx, c, item_name)
        if success:
            await self.config.user(ctx.author).set(await c.to_json(ctx, self.config))
            return await smart_embed(ctx, msg, success=True)
        return await smart_embed(ctx, msg, success=False)

    @commands.hybrid_command(name="duel")
    @commands.cooldown(rate=1, per=7200, type=commands.BucketType.user)
    async def duel(self, ctx: "commands.Context", member: Optional[discord.Member] = None):
        """Challenge another player to a duel (pvP skirmish)."""
        if member is None:
            return await smart_embed(ctx, _("Please @mention the player you want to duel."))
        if hasattr(self, "negaverse") and hasattr(self.negaverse, "duel"):
            try:
                return await self.negaverse.duel(ctx, member)
            except Exception:
                pass
        return await smart_embed(ctx, _("Duel functionality is not available; try negaverse or use duel via the UI."))

    @commands.hybrid_command(name="warzone")
    @commands.cooldown(rate=1, per=86400, type=commands.BucketType.guild)
    async def warzone(self, ctx: "commands.Context"):
        """Arena / event mode — stub for future implementation."""
        return await smart_embed(ctx, _("Warzone is not implemented yet. Stay tuned for events."))
