"""Collector commands: buy, assign, recall.

Collectors provide Supplies over time; these are simple command handlers that
update `Character.collectors` and `Character.collector_assignments`.
"""
from typing import Optional

try:
    from redbot.core import commands
except Exception:
    class commands:
        class hybrid_command:
            def __init__(self, *a, **k):
                pass

        class cooldown:
            def __init__(self, *a, **k):
                pass

        class bot_has_permissions:
            def __init__(self, *a, **k):
                pass

        class guild_only:
            def __init__(self, *a, **k):
                pass

from adventure.charsheet import Character
from adventure.helpers import smart_embed
import json
import asyncio
from pathlib import Path


async def _load_collectors_definitions(self):
    try:
        theme = await self.config.theme()
    except Exception:
        theme = "default"
    try:
        from redbot.core import data_manager

        # prefer cog_data_path (installed overrides) and fall back to bundled
        get_path = data_manager.cog_data_path
        fp = get_path(self) / f"{theme}" / "collectors.json"
        if not fp.exists():
            # try bundled
            fp = data_manager.bundled_data_path(self) / f"{theme}" / "collectors.json"
            if not fp.exists():
                # fallback to local repo layout (adventure/data/<theme>/collectors.json)
                local_fp = Path(__file__).parent / "data" / f"{theme}" / "collectors.json"
                if local_fp.exists():
                    fp = local_fp
                else:
                    return {}
        with open(fp, "r", encoding="utf-8") as fh:
            cfg = json.load(fh)
        return {c.get("id"): c for c in cfg.get("collectors", [])}
    except Exception:
        return {}


class CollectorCommands:
    """Collector mixin: buy/assign/recall with accrual support.

    Methods added:
    - `accrue_for_member(ctx, member, seconds=3600)`: accrue supplies for a single member for the given interval.
    - a background loop that periodically accrues for all members (started on cog_load).
    """

    _collector_task = None
    _collector_tick_seconds = 60

    async def cog_load(self):
        # start background accrual loop
        try:
            self._collector_task = asyncio.create_task(self._collector_loop())
        except Exception:
            self._collector_task = None

    def cog_unload(self):
        try:
            if self._collector_task:
                self._collector_task.cancel()
        except Exception:
            pass

    async def _collector_loop(self):
        # runs in background on the bot; iterates guild members and accrues small amounts
        while True:
            try:
                await asyncio.sleep(self._collector_tick_seconds)
                # iterate guild members to accrue; this is intentionally lightweight
                for guild in getattr(self, "bot", []).guilds if hasattr(self, "bot") else []:
                    for member in guild.members:
                        try:
                            # create a lightweight ctx-like object with required attrs
                            class _C:
                                def __init__(self, bot, guild, channel, author):
                                    self.bot = bot
                                    self.guild = guild
                                    self.channel = channel
                                    self.author = author

                            ctx = _C(getattr(self, "bot", None), guild, None, member)
                            await self.accrue_for_member(ctx, member, seconds=self._collector_tick_seconds)
                        except Exception:
                            continue
            except asyncio.CancelledError:
                break
            except Exception:
                # swallow exceptions to keep loop alive
                continue
    @commands.hybrid_command(name="collector buy")
    async def collector_buy(self, ctx: commands.Context, collector_id: Optional[str] = "worker"):
        try:
            c = await Character.from_json(ctx, self.config, ctx.author, self._daily_bonus)
        except Exception:
            return await smart_embed(ctx, "Unable to load character data.")
        # strict validation against collectors.json (deny unknown ids)
        defs = await _load_collectors_definitions(self)
        if not defs:
            return await smart_embed(ctx, "No collectors are defined for this theme.")
        if collector_id not in defs:
            return await smart_embed(ctx, f"Unknown collector id '{collector_id}'.")

        collectors = getattr(c, "collectors", {}) or {}
        collectors[collector_id] = collectors.get(collector_id, 0) + 1
        c.collectors = collectors
        await self.config.user(ctx.author).set(await c.to_json(ctx, self.config))
        return await smart_embed(ctx, f"Purchased collector '{collector_id}'. You now have {collectors[collector_id]}.", success=True)

    @commands.hybrid_command(name="collector assign")
    async def collector_assign(self, ctx: commands.Context, collector_id: Optional[str] = None, node_id: Optional[str] = None):
        if not collector_id or not node_id:
            return await smart_embed(ctx, "Specify a collector id and node id to assign (e.g. `collector assign chinook oil_derrick`).")
        try:
            c = await Character.from_json(ctx, self.config, ctx.author, self._daily_bonus)
        except Exception:
            return await smart_embed(ctx, "Unable to load character data.")

        collectors = getattr(c, "collectors", {}) or {}
        if collectors.get(collector_id, 0) <= 0:
            return await smart_embed(ctx, "You don't own that collector to assign.")
        # strict validation
        defs = await _load_collectors_definitions(self)
        if not defs:
            return await smart_embed(ctx, "No collectors are defined for this theme.")
        collector_def = defs.get(collector_id)
        if collector_def is None:
            return await smart_embed(ctx, f"Unknown collector id '{collector_id}'.")

        assignments = getattr(c, "collector_assignments", {}) or {}
        assignments.setdefault(collector_id, []).append(node_id)
        c.collector_assignments = assignments

        # immediate grant: give a small fraction of hourly rate to simulate starting yield
        if collector_def and isinstance(collector_def.get("rate_per_hour"), (int, float)):
            rate = int(collector_def.get("rate_per_hour", 0))
            immediate = max(1, rate // 24) if rate > 0 else 0
            if immediate:
                try:
                    c.supplies += int(immediate)
                except Exception:
                    c.supplies = getattr(c, "supplies", 0)

        await self.config.user(ctx.author).set(await c.to_json(ctx, self.config))
        return await smart_embed(ctx, f"Assigned {collector_id} to {node_id}.", success=True)

    async def accrue_for_member(self, ctx: commands.Context, member, seconds: int = 3600):
        """Accrue supplies for a single member based on assigned collectors.

        This is intended to be called by the background loop. It reads the
        character state, calculates pro-rated yield for the `seconds` interval
        and writes back the updated supplies.
        """
        try:
            c = await Character.from_json(ctx, self.config, member, self._daily_bonus)
        except Exception:
            return

        defs = await _load_collectors_definitions(self)
        if not defs:
            return

        assignments = getattr(c, "collector_assignments", {}) or {}
        total_gain = 0
        for col_id, nodes in assignments.items():
            col_def = defs.get(col_id)
            if not col_def:
                continue
            rate = int(col_def.get("rate_per_hour", 0))
            # prorate by seconds/3600
            gain = int(rate * (seconds / 3600.0))
            total_gain += gain * max(1, len(nodes))

        if total_gain > 0:
            try:
                c.supplies += int(total_gain)
            except Exception:
                pass
            await self.config.user(member).set(await c.to_json(ctx, self.config))

    @commands.hybrid_command(name="collector recall")
    async def collector_recall(self, ctx: commands.Context, collector_id: Optional[str] = None):
        if not collector_id:
            return await smart_embed(ctx, "Specify a collector id to recall.")
        try:
            c = await Character.from_json(ctx, self.config, ctx.author, self._daily_bonus)
        except Exception:
            return await smart_embed(ctx, "Unable to load character data.")

        assignments = getattr(c, "collector_assignments", {}) or {}
        if collector_id not in assignments:
            return await smart_embed(ctx, "That collector is not assigned.")
        assignments.pop(collector_id, None)
        c.collector_assignments = assignments
        await self.config.user(ctx.author).set(await c.to_json(ctx, self.config))
        return await smart_embed(ctx, f"Recalled {collector_id}.", success=True)
# -*- coding: utf-8 -*-
"""
Collector/Blackmarket commands for GeneralsRPG.
"""

from redbot.core import commands
from redbot.core.i18n import Translator
from adventure.ui.helpers import smart_embed

_ = Translator("Adventure", __file__)


class CollectorCommands:
    @commands.hybrid_command(name="blackmarket")
    async def blackmarket(self, ctx: commands.Context):
        """Access the black market for rare deals."""
        return await smart_embed(ctx, _("The black market is under construction..."))
