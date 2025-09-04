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

class Adventure(commands.GroupCog):
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
