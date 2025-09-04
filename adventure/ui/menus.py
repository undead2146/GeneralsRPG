from __future__ import annotations

from typing import List, Tuple, Dict, Any

import discord

try:
    from redbot.vendored.discord.ext import menus
except Exception:
    # Minimal fallback implementation used for tests and import-time stability.
    class _SimpleListPageSource:
        def __init__(self, entries: List[Any]):
            self.entries = list(entries)

        def get_page(self, page: int):
            per_page = 10
            start = page * per_page
            return self.entries[start : start + per_page]

    class menus:
        ListPageSource = _SimpleListPageSource


class LeaderboardSource(menus.ListPageSource):
    def __init__(self, entries: List[Tuple[int, Dict]]):
        super().__init__(entries)


class LeaderboardMenu(discord.ui.View):
    def __init__(self, source: LeaderboardSource, cog=None):
        super().__init__()
        self.source = source
        self.cog = cog

    async def start(self, ctx: discord.Interaction | discord.ext.commands.Context):
        # Lightweight start used by thin command wrappers in tests
        await ctx.send(str(list(self.source.entries)))


class LeaderboardSource:
    pass


class SimpleSource(menus.ListPageSource):
    def __init__(self, entries: List[Any]):
        super().__init__(entries)


class BackpackSource(menus.ListPageSource):
    def __init__(self, entries: List[Any]):
        super().__init__(entries)


class BackpackMenu(discord.ui.View):
    def __init__(self, source: BackpackSource, cog=None, **kwargs):
        super().__init__()
        self.source = source
        self.cog = cog

    async def start(self, ctx: discord.ext.commands.Context, page: int = 0):
        await ctx.send("\n".join(map(str, self.source.entries)))
