"""Legacy Adventure Cog kept for compatibility during refactor.

This file intentionally contains a compact placeholder for the original
Adventure implementation moved out of `adventure/adventure.py` so
`adventure/adventure.py` can become an import-time shim that prefers
`adventure.core.adventure.Adventure`.

The placeholder keeps imports light so it stays importable in test
environments. Full legacy implementation remains in repo history.
"""
# -*- coding: utf-8 -*-
import asyncio
from redbot.core import commands

_ = lambda s: s

try:
    from .commands.wrappers import WrapperCommands
except ImportError:
    # Fallback if wrapper commands can't be imported due to dependencies
    class WrapperCommands:
        async def skirmish(self, ctx, *, challenge=None):
            """Minimal skirmish implementation for legacy mode."""
            return await self._adventure(ctx, challenge=challenge)
        
        async def operation(self, ctx, *, challenge=None):
            """Minimal operation implementation for legacy mode."""
            return await self._adventure(ctx, challenge=challenge)
        
        async def drill(self, ctx, *, skill=None, amount=1):
            """Minimal drill implementation for legacy mode."""
            return await self.skill(ctx, skill=skill, amount=amount)

class Adventure(WrapperCommands, commands.GroupCog):
    """A compact legacy placeholder for the original Adventure class.

    The real implementation lives in the original `adventure/adventure.py` and
    is preserved in git history. This placeholder is only used as a fallback
    when importing the refactored core implementation fails.
    """

    __version__ = "legacy-4.1.2"

    def __init__(self, bot):
        self.bot = bot
        self._ready_event = asyncio.Event()

    async def initialize(self):
        await self.bot.wait_until_red_ready()
        self._ready_event.set()
    
    async def _adventure(self, ctx, *, challenge=None):
        """Minimal placeholder for adventure method."""
        return await ctx.send("Adventure functionality not fully loaded (legacy mode)")
    
    async def skill(self, ctx, *, skill=None, amount=1):
        """Minimal placeholder for skill method."""
        return await ctx.send("Skill functionality not fully loaded (legacy mode)")
