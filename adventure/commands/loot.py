# -*- coding: utf-8 -*-
import asyncio
import logging
import random
import time
from typing import Optional, Union

import discord
from typing import Any, Dict, List
try:
    # Prefer core implementation when available
    from adventure.core.rewards import RewardEngine
except Exception:
    try:
        from ..rewards import RewardEngine
    except Exception:
        try:
            from adventure.rewards import RewardEngine
        except Exception:
            RewardEngine = None
try:
    from redbot.core import commands
    from redbot.core.errors import BalanceTooHigh
    from redbot.core.i18n import Translator
    from redbot.core.utils import AsyncIter
    from redbot.core.utils.chat_formatting import bold, box, humanize_list, humanize_number
except Exception:  # pragma: no cover - provide minimal fallbacks for test environments
    class commands:
        class Cog:
            pass

        class hybrid_command:
            def __init__(self, *a, **k):
                pass
            def __call__(self, func):
                return func

        class bot_has_permissions:
            def __init__(self, *a, **k):
                pass
            def __call__(self, func):
                return func

        class cooldown:
            def __init__(self, *a, **k):
                pass
            def __call__(self, func):
                return func
        
        class BucketType:
            """Minimal BucketType replacement for tests."""
            # common bucket types used by decorators in the codebase
            default = 0
            user = 1
            guild = 2
            channel = 3
            member = 4

        class Context:
            """Minimal Context stub used only for type hints in tests."""
            pass

    class BalanceTooHigh(Exception):
        pass

    def Translator(name, file):
        return lambda s: s

    class AsyncIter:
        pass

    def bold(x):
        return str(x)

    def box(x, lang=None):
        return str(x)

    def humanize_list(x):
        return ", ".join(x) if isinstance(x, (list, tuple)) else str(x)

    def humanize_number(x):
        return str(x)

try:
    from ..abc import AdventureMixin
    from ..bank import bank
    from ..charsheet import Character, Item
    from ..constants import Rarities, Slot
    from ..converters import RarityConverter
    from ..helpers import LootView, _sell, escape, is_dev, smart_embed
    from ..menus import BackpackMenu, BackpackSource
except Exception:
    # When tests load this file directly (spec_from_file_location) the module may not
    # have a package context for relative imports; fall back to absolute imports.
    from adventure.abc import AdventureMixin
    from adventure.bank import bank
    from adventure.charsheet import Character, Item
    from adventure.constants import Rarities, Slot
    from adventure.converters import RarityConverter
    from adventure.helpers import LootView, _sell, escape, is_dev, smart_embed
    from adventure.menus import BackpackMenu, BackpackSource

_ = Translator("Adventure", __file__)

log = logging.getLogger("red.cogs.adventure")


class LootCommands(AdventureMixin):
    """This class will handle Loot interactions"""

    @commands.hybrid_command(name="loot")
    @commands.bot_has_permissions(add_reactions=True)
    @commands.cooldown(rate=1, per=4, type=commands.BucketType.user)
    async def loot(
        self,
        ctx: commands.Context,
        box_type: Optional[RarityConverter] = None,
        number: int = 1,
    ):
        if not await self.allow_in_dm(ctx):
            return await smart_embed(ctx, _("This command is not available in DM's on this bot."))
        async with ctx.typing():
            async with self.get_lock(ctx.author):
                msgs = []
                try:
                    c = await Character.from_json(ctx, self.config, ctx.author, self._daily_bonus)
                except Exception as exc:
                    log.exception("Error with the new character sheet", exc_info=exc)
                    return
                if box_type is None:
                    chests = c.treasure.ansi
                    return await ctx.send(
                        box(
                            _("{author} owns {chests} chests.").format(
                                author=escape(ctx.author.display_name),
                                chests=chests,
                            ),
                            lang="ansi",
                        )
                    )
                if c.is_backpack_full(is_dev=is_dev(ctx.author)):
                    await ctx.send(
                        _("{author}, your backpack is currently full.").format(author=bold(ctx.author.display_name))
                    )
                    return
                if not box_type.is_chest:
                    return await smart_embed(
                        ctx,
                        _("There is talk of a {} treasure chest but nobody ever saw one.").format(box_type.get_name()),
                    )
                redux = box_type.value
                treasure = c.treasure[redux]
                if treasure < 1 or treasure < number:
                    await smart_embed(
                        ctx,
                        _("{author}, you do not have enough {box} treasure chests to open.").format(
                            author=bold(ctx.author.display_name), box=box_type
                        ),
                    )
                    return
                else:
                    if number > 1:
                        # atomically save reduced loot count then lock again when saving inside
                        # open chests
                        c.treasure[redux] -= number
                        await self.config.user(ctx.author).set(await c.to_json(ctx, self.config))
                        items = await self._open_chests(ctx, box_type, number, character=c)
                        msg = _("{}, you've opened the following items:\n\n").format(escape(ctx.author.display_name))
                        rows = []
                        async for index, item in AsyncIter(items.values(), steps=100).enumerate(start=1):
                            rows.append(item)
                        tables = await c.make_backpack_tables(rows, msg)
                        for t in tables:
                            msgs.append(t)
                    else:
                        # atomically save reduced loot count then lock again when saving inside
                        # open chests
                        c.treasure[redux] -= 1
                        await self.config.user(ctx.author).set(await c.to_json(ctx, self.config))
                        await self._open_chest(ctx, ctx.author, box_type, character=c)
                        # returns item and msg
        if msgs:
            await BackpackMenu(
                source=BackpackSource(msgs),
                cog=self,
                delete_message_after=True,
                clear_reactions_after=True,
                timeout=60,
                help_command=self.loot,
            ).start(ctx=ctx)

    async def _genitem(self, ctx: commands.Context, rarity: Optional[Rarities] = None, slot: Optional[Slot] = None):
        """Generate an item."""
        if rarity is Rarities.set:
            items = list(self.TR_GEAR_SET.items())
            items = (
                [
                    i
                    for i in items
                    if i[1]["slot"] == [slot.value] or (slot is Slot.two_handed and len(i[1]["slot"]) > 1)
                ]
                if slot
                else items
            )
            item_name, item_data = random.choice(items)
            return Item.from_json(ctx, {item_name: item_data})

        if rarity is None:
            rarity = Rarities.normal
        if slot is None:
            slot = random.choice([i for i in Slot])
        name = ""
        stats = {"att": 0, "cha": 0, "int": 0, "dex": 0, "luck": 0}

        def add_stats(word_stats):
            """Add stats in word's dict to local stats dict."""
            for stat in stats.keys():
                if stat in word_stats:
                    stats[stat] += word_stats[stat]

        # only rare and above should have prefix with PREFIX_CHANCE
        prefix_chance = rarity.prefix_chance()
        if prefix_chance is not None and random.random() <= prefix_chance:
            #  log.debug(f"Prefix %: {PREFIX_CHANCE[rarity]}")
            prefix, prefix_stats = random.choice(list(self.PREFIXES.items()))
            name += f"{prefix} "
            add_stats(prefix_stats)

        material, material_stat = random.choice(list(self.MATERIALS[rarity.name].items()))
        name += f"{material} "
        for stat in stats.keys():
            stats[stat] += material_stat

        equipment, equipment_stats = random.choice(list(self.EQUIPMENT[slot.value].items()))
        name += f"{equipment}"
        add_stats(equipment_stats)

        suffix_chance = rarity.suffix_chance()
        # only epic and above should have suffix with SUFFIX_CHANCE
        if suffix_chance is not None and random.random() <= suffix_chance:
            #  log.debug(f"Suffix %: {SUFFIX_CHANCE[rarity]}")
            suffix, suffix_stats = random.choice(list(self.SUFFIXES.items()))
            of_keyword = "of" if "the" not in suffix_stats else "of the"
            name += f" {of_keyword} {suffix}"
            add_stats(suffix_stats)

        # slot_list = [slot] if slot != "two handed" else ["left", "right"]
        return Item(
            ctx=ctx,
            name=name,
            slot=slot.to_json(),
            rarity=rarity.name,
            att=stats["att"],
            int=stats["int"],
            cha=stats["cha"],
            dex=stats["dex"],
            luck=stats["luck"],
            owned=1,
            parts=1,
        )

    @commands.hybrid_command(name="convert")
    @commands.cooldown(rate=1, per=4, type=commands.BucketType.guild)
    async def convert(
        self,
        ctx: commands.Context,
        box_rarity: RarityConverter,
        amount: int = 1,
    ):
        """Convert normal, rare or epic chests.

        Trade 25 normal chests for 1 rare chest.
        Trade 25 rare chests for 1 epic chest.
        Trade 25 epic chests for 1 legendary chest.
        """

        # Thanks to flare#0001 for the idea and writing the first instance of this
        if self.in_adventure(ctx):
            return await smart_embed(
                ctx,
                _(
                    "You tried to magically combine some of your loot chests "
                    "but the monster ahead is commanding your attention."
                ),
            )
        costs = {
            Rarities.normal: 25,
            Rarities.rare: 25,
            Rarities.epic: 25,
        }
        if box_rarity not in costs.keys():
            await smart_embed(
                ctx,
                _("{user}, please select between {boxes} treasure chests to convert.").format(
                    user=bold(ctx.author.display_name),
                    boxes=humanize_list([i.get_name() for i in costs.keys()]),
                ),
            )
            return

        rebirth_normal = 2
        rebirth_rare = 8
        rebirth_epic = 10
        if amount < 1:
            return await smart_embed(ctx, _("Nice try :smirk:"))
        if amount > 1:
            plural = "s"
        else:
            plural = ""
        async with self.get_lock(ctx.author):
            try:
                c = await Character.from_json(ctx, self.config, ctx.author, self._daily_bonus)
            except Exception as exc:
                log.exception("Error with the new character sheet", exc_info=exc)
                return

            if box_rarity is Rarities.rare and c.rebirths < rebirth_rare:
                return await smart_embed(
                    ctx,
                    ("{user}, you need to have {rebirth} or more rebirths to convert rare treasure chests.").format(
                        user=bold(ctx.author.display_name), rebirth=rebirth_rare
                    ),
                )
            elif box_rarity is Rarities.epic and c.rebirths < rebirth_epic:
                return await smart_embed(
                    ctx,
                    ("{user}, you need to have {rebirth} or more rebirths to convert epic treasure chests.").format(
                        user=bold(ctx.author.display_name), rebirth=rebirth_epic
                    ),
                )
            elif c.rebirths < 2:
                return await smart_embed(
                    ctx,
                    _("{c}, you need to 3 rebirths to use this.").format(c=bold(ctx.author.display_name)),
                )
            msg = ""
            success_msg = _(
                "Successfully converted {converted} treasure "
                "chests to {to} treasure chest{plur}.\n{author} "
                "now owns {chests} treasure chests."
            )
            failed_msg = _("{author}, you do not have {amount} treasure chests to convert.")
            if box_rarity is Rarities.normal and c.rebirths >= rebirth_normal:
                rarity = Rarities.normal
                to_rarity = Rarities.rare
                converted = rarity.rarity_colour.as_str(f"{humanize_number(costs[rarity] * amount)} {rarity}")
                if c.treasure.normal >= (costs[rarity] * amount):
                    c.treasure.normal -= costs[rarity] * amount
                    c.treasure.rare += 1 * amount
                    to = to_rarity.rarity_colour.as_str(f"{humanize_number(1 * amount)} {to_rarity}")
                    msg = success_msg.format(
                        converted=converted,
                        to=to,
                        plur=plural,
                        author=escape(ctx.author.display_name),
                        chests=c.treasure.ansi,
                    )
                    await self.config.user(ctx.author).set(await c.to_json(ctx, self.config))
                else:
                    msg = failed_msg.format(author=escape(ctx.author.display_name), amount=converted)
            elif box_rarity is Rarities.rare and c.rebirths >= rebirth_rare:
                rarity = Rarities.rare
                to_rarity = Rarities.epic
                converted = rarity.rarity_colour.as_str(f"{humanize_number(costs[rarity] * amount)} {rarity}")
                if c.treasure.rare >= (costs[rarity] * amount):
                    c.treasure.rare -= costs[rarity] * amount
                    c.treasure.epic += 1 * amount
                    to = to_rarity.rarity_colour.as_str(f"{humanize_number(1 * amount)} {to_rarity}")
                    msg = success_msg.format(
                        converted=converted,
                        to=to,
                        plur=plural,
                        author=escape(ctx.author.display_name),
                        chests=c.treasure.ansi,
                    )
                    await self.config.user(ctx.author).set(await c.to_json(ctx, self.config))
                else:
                    msg = failed_msg.format(author=escape(ctx.author.display_name), amount=converted)
            elif box_rarity is Rarities.epic and c.rebirths >= rebirth_epic:
                rarity = Rarities.epic
                to_rarity = Rarities.legendary
                converted = rarity.rarity_colour.as_str(f"{humanize_number(costs[rarity] * amount)} {rarity}")
                if c.treasure.epic >= (costs[rarity] * amount):
                    c.treasure.epic -= costs[rarity] * amount
                    c.treasure.legendary += 1 * amount
                    to = to_rarity.rarity_colour.as_str(f"{humanize_number(1 * amount)} {to_rarity}")
                    msg = success_msg.format(
                        converted=converted,
                        to=to,
                        plur=plural,
                        author=escape(ctx.author.display_name),
                        chests=c.treasure.ansi,
                    )
                    await self.config.user(ctx.author).set(await c.to_json(ctx, self.config))
                else:
                    msg = failed_msg.format(author=escape(ctx.author.display_name), amount=converted)
            await ctx.send(box(msg, lang="ansi"))

    async def _open_chests(
        self,
        ctx: commands.Context,
        chest_type: Rarities,
        amount: int,
        character: Character,
    ):
        items = {}
        async for _loop_counter in AsyncIter(range(0, max(amount, 0)), steps=100):
            item = await self._roll_chest(chest_type, character)
            item_name = str(item)
            if item_name in items:
                items[item_name].owned += 1
            else:
                items[item_name] = item
            await character.add_to_backpack(item)
        await self.config.user(ctx.author).set(await character.to_json(ctx, self.config))
        return items

    async def _open_chest(self, ctx: commands.Context, user: discord.User, chest_type: Rarities, character: Character):
        pet = character.heroclass.get("pet", {}).get("name", "No Pet?")
        if chest_type is not Rarities.pet:
            chest_msg = _("{} is opening a treasure chest. What riches lay inside?").format(escape(user.display_name))
        else:
            chest_msg = _("{user}'s {pet} is foraging for treasure. What will it find?").format(
                user=escape(ctx.author.display_name), pet=pet
            )
        open_msg = await ctx.send(box(chest_msg, lang="ansi"))
        await asyncio.sleep(2)
        item = await self._roll_chest(chest_type, character)
        if chest_type == "pet" and not item:
            await open_msg.edit(
                content=box(
                    _("{c_msg}\nThe {user} found nothing of value.").format(c_msg=chest_msg, user=pet),
                    lang="ansi",
                )
            )
            return None
        table = item.table(character)
        slot = item.slot
        old_item = getattr(character, item.slot.char_slot, None)
        old_stats = ""

        if old_item:
            old_item_name, old_item_row = old_item.row(character)
            table.rows.append([_("Currently Equipped\n") + old_item_name])
            table.rows.append(old_item_row)
        view = LootView(60, ctx.author)

        old_stats = str(table)
        if chest_type is not Rarities.pet:
            chest_msg2 = _("{user} found {item}.\n").format(user=escape(user.display_name), item=item.ansi)
        else:
            chest_msg2 = _("{user}'s' {pet} found {item}.\n").format(
                user=escape(user.display_name),
                pet=pet,
                item=item.ansi,
            )
        await open_msg.edit(
            content=box(
                _(
                    "{c_msg}\n\n{c_msg_2}\n\nDo you want to equip "
                    "this item, put in your backpack, or sell this item?\n\n"
                    "{old_stats}"
                ).format(c_msg=chest_msg, c_msg_2=chest_msg2, old_stats=old_stats),
                lang="ansi",
            ),
            view=view,
        )
        await view.wait()
        if view.result.value == 0:
            await self._clear_react(open_msg)

    # --- GeneralsRPG action handlers ---
    async def _load_theme_json(self, name: str):
        """Return parsed JSON for the current theme or None if not found."""
        try:
            theme = await self.config.theme()
            if theme in {"default"}:
                get_path = bundled_data_path
            else:
                get_path = cog_data_path
            fp = get_path(self) / theme / f"{name}.json"
            if not fp.exists():
                fp = bundled_data_path(self) / "default" / f"{name}.json"
            return json.loads(fp.read_text())
        except Exception:
            log.exception("Failed to load theme json: %s", name)
            return None

    async def _pick_drop(self, drops: list):
        """Simple drop resolution based on chance percentages in a list of drop dicts."""
        chosen = []
        for d in drops:
            chance = d.get("chance", 0)
            roll = random.randint(1, 100)
            if roll <= chance:
                amt = d.get("amount", [1, 1])
                if isinstance(amt, list) and len(amt) == 2:
                    amount = random.randint(amt[0], amt[1])
                else:
                    amount = int(amt)
                chosen.append((d.get("name"), amount))
        return chosen

    def _map_drop_to_item(self, ctx: commands.Context, name: str, amount: int) -> Item:
        """Map a drop name to a minimal Item with simple economy semantics.

        Initial mapping (simple):
        - names containing 'blueprint' -> blueprint event items (rarity 'event')
        - names containing 'part' or 'scrap' or 'component' -> parts (rarity 'normal', parts=amount)
        - fallback -> generic supplies (rarity 'normal')
        """
        lname = name.lower()
        # Blueprint -> event item
        if "blueprint" in lname or "blue print" in lname:
            return Item(ctx=ctx, name=name, slot=["chest"], rarity="event", owned=amount, parts=0)

        # Parts / scrap -> items that carry `parts` so recipes can consume them
        if any(k in lname for k in ("part", "parts", "scrap", "component", "components")):
            return Item(ctx=ctx, name=name, slot=["chest"], rarity="normal", owned=amount, parts=amount)

        # Supplies / credits -> map to a canonical Supplies item so economy UI is consistent
        if any(k in lname for k in ("supply", "supplies", "credit", "credits", "supplycrate", "supply crate")):
            return Item(ctx=ctx, name="Supplies", slot=[], rarity="normal", owned=amount, parts=0)

        # Command Points / CP -> special craft currency
        if any(k in lname for k in ("command point", "command points", "cp", "cmdpt")):
            return Item(ctx=ctx, name="Command Point", slot=[], rarity="normal", owned=amount, parts=0)

        # fallback: generic named item (keeps original name)
        return Item(ctx=ctx, name=name, slot=[], rarity="normal", owned=amount, parts=0)

    async def gather_action(self, ctx: commands.Context, area: Optional[object] = None):
        """Handle gather command: add supplies/materials to backpack."""
        if not await self.allow_in_dm(ctx):
            return await smart_embed(ctx, _("This command is not available in DM's on this bot."))
        async with self.get_lock(ctx.author):
            try:
                c = await Character.from_json(ctx, self.config, ctx.author, self._daily_bonus)
            except Exception as exc:
                log.exception("Error loading character for gather", exc_info=exc)
                return
            # Delegate to centralized worker for consistent behavior and easier testing
            ok, msg = await self.do_work(ctx, c, "gather")
            if not ok:
                return await smart_embed(ctx, msg)
            await smart_embed(ctx, msg)

    async def salvage_action(self, ctx: commands.Context, wreck: Optional[object] = None):
        """Handle salvage command: add vehicle parts or rare components."""
        if not await self.allow_in_dm(ctx):
            return await smart_embed(ctx, _("This command is not available in DM's on this bot."))
        async with self.get_lock(ctx.author):
            try:
                c = await Character.from_json(ctx, self.config, ctx.author, self._daily_bonus)
            except Exception as exc:
                log.exception("Error loading character for salvage", exc_info=exc)
                return
            ok, msg = await self.do_work(ctx, c, "salvage")
            if not ok:
                return await smart_embed(ctx, msg)
            await smart_embed(ctx, msg)

    async def blackmarket_action(self, ctx: commands.Context, deal: Optional[object] = None):
        """Handle blackmarket command: high risk / high reward drops with optional loss."""
        if not await self.allow_in_dm(ctx):
            return await smart_embed(ctx, _("This command is not available in DM's on this bot."))
        async with self.get_lock(ctx.author):
            try:
                c = await Character.from_json(ctx, self.config, ctx.author, self._daily_bonus)
            except Exception as exc:
                log.exception("Error loading character for blackmarket", exc_info=exc)
                return
            ok, msg = await self.do_work(ctx, c, "blackmarket")
            if not ok:
                return await smart_embed(ctx, msg)
            await smart_embed(ctx, msg)
            return

    async def do_work(self, ctx: commands.Context, character: Character, category: str):
        """Centralized worker for gather/salvage/blackmarket flows.

        Returns (success: bool, message: str).
        """
        try:
            # Prefer a dedicated rewards.json for simple deterministic reward mapping
            rewards_cfg = None
            try:
                rewards_cfg = await self._load_theme_json("rewards")
            except Exception:
                rewards_cfg = None

            # If a rewards config exists and contains an entry for this category,
            # use the RewardEngine to produce per-user rewards. This provides a
            # compact, testable, and theme-driven reward path. The rewards.json
            # may contain numeric ranges for supplies/parts/cp (e.g. [min,max])
            # or fixed integers. We attempt to apply numeric grants via
            # Character.add_supplies/add_cp when available and fall back to
            # mapping drops to backpack Items when those methods are missing.
            if rewards_cfg and RewardEngine is not None and category in rewards_cfg:
                try:
                    engine = RewardEngine(rewards_cfg, rng=random.Random())
                    participants = [{"id": getattr(ctx.author, "id", None)}]
                    reward_map = engine.calculate(category, participants, None)
                    user_rewards = reward_map.get(int(getattr(ctx.author, "id", 0)), {})

                    # Apply rewards to character and build a friendly summary message
                    awarded = []
                    # supplies
                    supplies_amt = user_rewards.get("supplies")
                    if supplies_amt:
                        try:
                            await character.add_supplies(int(supplies_amt))
                            awarded.append(_("+{amt} Supplies").format(amt=humanize_number(int(supplies_amt))))
                        except Exception:
                            item = self._map_drop_to_item(ctx, "Supplies", int(supplies_amt))
                            await character.add_to_backpack(item, number=int(supplies_amt))
                            awarded.append(_("+{amt} Supplies (backpack)").format(amt=humanize_number(int(supplies_amt))))

                    # parts
                    parts_amt = user_rewards.get("parts")
                    if parts_amt:
                        try:
                            # represent parts as backpack items so recipes can consume them
                            item = self._map_drop_to_item(ctx, "Parts", int(parts_amt))
                            await character.add_to_backpack(item, number=int(parts_amt))
                            awarded.append(_("+{amt} Parts").format(amt=humanize_number(int(parts_amt))))
                        except Exception:
                            pass

                    # command points
                    cp_amt = user_rewards.get("cp")
                    if cp_amt:
                        try:
                            await character.add_cp(int(cp_amt))
                            awarded.append(_("+{amt} CP").format(amt=humanize_number(int(cp_amt))))
                        except Exception:
                            item = self._map_drop_to_item(ctx, "Command Point", int(cp_amt))
                            await character.add_to_backpack(item, number=int(cp_amt))
                            awarded.append(_("+{amt} CP (backpack)").format(amt=humanize_number(int(cp_amt))))

                    # blueprints
                    bp_amt = user_rewards.get("blueprints")
                    if bp_amt:
                        try:
                            for _ in range(int(bp_amt)):
                                bp_item = self._map_drop_to_item(ctx, "Blueprint", 1)
                                await character.add_to_backpack(bp_item, number=1)
                            awarded.append(_("+{amt} Blueprint(s)").format(amt=humanize_number(int(bp_amt))))
                        except Exception:
                            pass

                    # persist and return friendly message with a compact summary
                    await self.config.user(ctx.author).set(await character.to_json(ctx, self.config))
                    if awarded:
                        summary = ", ".join(awarded)
                    else:
                        summary = _("No resources awarded.")
                    if category == "salvage":
                        return True, _("Salvage complete: {summary}").format(summary=summary)
                    if category == "blackmarket":
                        return True, _("Black market run complete: {summary}").format(summary=summary)
                    return True, _("Gather complete: {summary}").format(summary=summary)
                except Exception as exc:
                    log.exception("RewardEngine path failed: %s", exc, exc_info=exc)
                    # fall through to legacy drop handling

            # legacy drop handling (fallback)
            data = await self._load_theme_json(category)
            if not data:
                return False, _("No data found for this activity.")
            # risk handling for blackmarket
            if category == "blackmarket":
                risk = data.get("risk", {})
                lose_chance = risk.get("lose_chance", 0)
                if lose_chance and random.randint(1, 100) <= lose_chance:
                    return False, _("Your black market run was intercepted; you lost your goods.")

            drops = data.get("drops", [])
            picked = await self._pick_drop(drops)
            if not picked:
                if category == "salvage":
                    return False, _("Salvaging failed; you found nothing usable.")
                if category == "gather":
                    return False, _("You searched the area but found nothing of value.")
                return False, _("Nothing to show.")

            for name, amt in picked:
                lname = name.lower()
                # handle numeric economy drops (supplies / command points)
                if "supply" in lname or "supplies" in lname or "credit" in lname:
                    # persist as numeric supplies
                    try:
                        await character.add_supplies(amt)
                    except Exception:
                        # if method missing or fails, fallback to backpack item
                        item = self._map_drop_to_item(ctx, name, amt)
                        await character.add_to_backpack(item, number=amt)
                    continue
                if "command point" in lname or lname == "cp" or "cmdpt" in lname:
                    try:
                        await character.add_cp(amt)
                    except Exception:
                        item = self._map_drop_to_item(ctx, name, amt)
                        await character.add_to_backpack(item, number=amt)
                    continue

                item = self._map_drop_to_item(ctx, name, amt)
                # Character.add_to_backpack may return False on failure. Handle conservatively.
                added = await character.add_to_backpack(item, number=amt)
                # add_to_backpack in current implementation doesn't return False; assume success.

            await self.config.user(ctx.author).set(await character.to_json(ctx, self.config))
            # friendly message per category
            if category == "salvage":
                return True, _("You salvaged parts and added them to your backpack.")
            if category == "blackmarket":
                return True, _("Black market acquisition complete; goods added to your backpack.")
            return True, _("You gathered some supplies and materials.")
        except Exception as exc:
            log.exception("Error in do_work: %s", exc, exc_info=exc)
            return False, _("An error occurred while performing the activity.")


async def craft_from_blueprint(ctx: commands.Context, character: Character, blueprint_name: str):
    """Attempt to craft an item using a blueprint Item in the character's backpack.

    Returns (success: bool, message: str).
    """
    try:
        lname = blueprint_name.lower()
        # recipe lookup: try to load per-theme recipes.json first, fall back to in-code RECIPES
        RECIPES = {}
        try:
            theme_recipes = None
            if hasattr(character, "cog") and character.cog is not None and hasattr(character.cog, "_load_theme_json"):
                try:
                    theme_recipes = await character.cog._load_theme_json("recipes")
                except Exception:
                    theme_recipes = None
            if theme_recipes and isinstance(theme_recipes, dict):
                RECIPES = theme_recipes
        except Exception:
            RECIPES = {}

        # find a matching blueprint item
        for key, item in list(character.backpack.items()):
            try:
                rarity_name = item.rarity.name.lower()
            except Exception:
                rarity_name = getattr(item, "rarity", "").lower()
            if rarity_name == "event" and lname in item.name.lower():
                # Determine recipe (best-effort match by product keyword)
                recipe = None
                for frag, r in RECIPES.items():
                    if frag in item.name.lower() or frag in lname:
                        recipe = r
                        break

                # If recipe exists, ensure character has required parts/supplies
                if recipe:
                    req_parts = int(recipe.get("parts", 0))
                    req_supplies = int(recipe.get("supplies", 0))
                    # count parts/supplies in backpack and include numeric fields
                    total_parts = 0
                    total_supplies = 0
                    # numeric supplies on character take precedence
                    try:
                        total_supplies += int(getattr(character, "supplies", 0))
                    except Exception:
                        pass
                    try:
                        total_parts += 0
                    except Exception:
                        pass
                    for p in character.backpack.values():
                        # items with 'parts' property indicate parts stacks
                        try:
                            total_parts += int(getattr(p, "parts", 0)) * int(getattr(p, "owned", 1))
                        except Exception:
                            pass
                        # supplies represented as items named 'supplies' or 'supply'
                        try:
                            if isinstance(getattr(p, "name", ""), str) and ("supply" in p.name.lower() or "supplies" in p.name.lower()):
                                total_supplies += int(getattr(p, "owned", 1))
                        except Exception:
                            pass

                    if total_parts < req_parts:
                        return False, _("You don't have enough parts to build this item (need {need}).").format(need=req_parts)
                    if total_supplies < req_supplies:
                        return False, _("You don't have enough supplies to build this item (need {need}).").format(need=req_supplies)

                    # consume required parts and supplies, track what we changed for rollback
                    parts_to_consume = req_parts
                    supplies_to_consume = req_supplies
                    consumed_parts = []  # list of (pkey, units_consumed)
                    consumed_supplies = []
                    consumed_numeric_supplies = 0
                    # Prefer consuming numeric supplies on the character first
                    if supplies_to_consume > 0:
                        try:
                            available_numeric = int(getattr(character, "supplies", 0))
                        except Exception:
                            available_numeric = 0
                        if available_numeric > 0:
                            take = min(available_numeric, supplies_to_consume)
                            try:
                                character.supplies = max(0, character.supplies - take)
                                consumed_numeric_supplies += take
                                supplies_to_consume -= take
                            except Exception:
                                # if numeric field cannot be modified, fall back to backpack supplies
                                consumed_numeric_supplies = 0

                    # consume parts from items with parts>0 first
                    for pkey, p in list(character.backpack.items()):
                        p_parts_per_unit = int(getattr(p, "parts", 0))
                        p_owned = int(getattr(p, "owned", 1))
                        p_parts = p_parts_per_unit * p_owned
                        if p_parts <= 0:
                            continue
                        if parts_to_consume <= 0:
                            break
                        # determine how many owned units to consume
                        units = min(p_owned, (parts_to_consume + max(p_parts_per_unit, 1) - 1) // max(p_parts_per_unit, 1))
                        try:
                            p.owned -= units
                        except Exception:
                            pass
                        consumed_parts.append((pkey, units))
                        parts_to_consume -= units * max(p_parts_per_unit, 1)
                        if getattr(p, "owned", 0) <= 0:
                            try:
                                del character.backpack[pkey]
                            except Exception:
                                pass

                    # consume supplies from backpack items (if still required)
                    if supplies_to_consume > 0:
                        for pkey, p in list(character.backpack.items()):
                            if supplies_to_consume <= 0:
                                break
                            try:
                                if isinstance(getattr(p, "name", ""), str) and ("supply" in p.name.lower() or "supplies" in p.name.lower()):
                                    p_owned = int(getattr(p, "owned", 1))
                                    take = min(p_owned, supplies_to_consume)
                                    try:
                                        p.owned -= take
                                    except Exception:
                                        pass
                                    consumed_supplies.append((pkey, take))
                                    supplies_to_consume -= take
                                    if getattr(p, "owned", 0) <= 0:
                                        try:
                                            del character.backpack[pkey]
                                        except Exception:
                                            pass
                            except Exception:
                                continue

                    # At this point parts_to_consume and supplies_to_consume should be satisfied.
                    # Create the crafted product and add to backpack.
                    product_name = recipe.get("product", item.name)
                    product_rarity = recipe.get("rarity", "normal")
                    try:
                        crafted = Item(ctx=ctx, name=product_name, slot=["chest"], rarity=product_rarity, owned=1, parts=0)
                        await character.add_to_backpack(crafted, number=1)
                        await self.config.user(ctx.author).set(await character.to_json(ctx, self.config))
                        return True, _("Successfully crafted {product}.").format(product=product_name)
                    except Exception as exc:
                        # Rollback best-effort: restore consumed amounts
                        try:
                            for pkey, units in consumed_parts:
                                p = character.backpack.get(pkey)
                                if p is not None:
                                    try:
                                        p.owned += units
                                    except Exception:
                                        pass
                            for pkey, units in consumed_supplies:
                                p = character.backpack.get(pkey)
                                if p is not None:
                                    try:
                                        p.owned += units
                                    except Exception:
                                        pass
                            if consumed_numeric_supplies > 0:
                                try:
                                    character.supplies = getattr(character, "supplies", 0) + consumed_numeric_supplies
                                except Exception:
                                    pass
                        except Exception:
                            pass
                        log.exception("Error while crafting product: %s", exc, exc_info=exc)
                        return False, _("Crafting failed due to an unexpected error.")

        # No matching blueprint or recipe was found
        return False, _("No matching blueprint found in backpack.")
    except Exception as exc:
        log.exception("Unhandled error in craft_from_blueprint: %s", exc, exc_info=exc)
        return False, _("An unexpected error occurred while attempting to craft the blueprint.")
