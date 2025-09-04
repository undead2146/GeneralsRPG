"""Core Adventure skeleton.

This module provides a lightweight, importable skeleton for the refactored
Adventure Cog. It is intentionally small and delegates heavy logic to other
`adventure.core.*` modules.
"""
from __future__ import annotations

import asyncio
import contextlib
import logging
from abc import ABC
from types import SimpleNamespace
from typing import Dict, MutableMapping

import discord
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.i18n import Translator, cog_i18n

_ = Translator("Adventure", __file__)
log = logging.getLogger("red.cogs.adventure.core")

_SCHEMA_VERSION = 4


class CompositeMetaClass(type(commands.Cog), type(ABC)):
    """Allows Cog metaclass to coexist with ABC metaclass."""


@cog_i18n(_)
class Adventure(commands.GroupCog, metaclass=CompositeMetaClass):
    """Thin Adventure Cog shell that wires core and command mixins.

    The full game behaviour lives in `adventure.core.*` modules and in the
    command mixins under `adventure.commands.*`.
    """

    __version__ = "0.0.0-core-skeleton"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, 2_710_801_001, force_registration=True)
        self._sessions: MutableMapping[int, object] = {}
        self.tasks = {}
        self.locks: MutableMapping[int, asyncio.Lock] = {}
        self.emojis = SimpleNamespace()
        self._ready_event = asyncio.Event()

        # Start background tasks as needed by the cog lifecycle
        self.cleanup_loop = self.bot.loop.create_task(self._cleanup_tasks())

    async def _cleanup_tasks(self):
        await self._ready_event.wait()
        while self is self.bot.get_cog("Adventure"):
            to_delete = [msg_id for msg_id, task in list(self.tasks.items()) if getattr(task, "done", lambda: False)()]
            for task_id in to_delete:
                try:
                    del self.tasks[task_id]
                except Exception:
                    pass
            await asyncio.sleep(300)

    def get_lock(self, member: discord.User) -> asyncio.Lock:
        if member.id not in self.locks:
            self.locks[member.id] = asyncio.Lock()
        return self.locks[member.id]
